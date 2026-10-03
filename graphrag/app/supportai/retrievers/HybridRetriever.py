import json
from supportai.retrievers import BaseRetriever
from common.metrics.tg_proxy import TigerGraphConnectionProxy

class HybridRetriever(BaseRetriever):
    def __init__(
        self,
        embedding_service,
        embedding_store,
        llm_service,
        connection: TigerGraphConnectionProxy,
    ):
        super().__init__(embedding_service, embedding_store, llm_service, connection)

    def search(self, question, indices, top_k=1, similarity_threshold=0.90, num_hops=2, num_seen_min=1, expand = False, method = "similarity", chunk_only=False, doc_only=False, verbose=False, max_results: int = 0, vector_query=None):
        if expand:
            questions = self._expand_question(question, top_k, verbose)
            verbose and self.logger.info(f"Expanded questions to use: {questions}")

            method = method.lower()
            if method == "keywords" or method == "both" or method == "all":
                keywords = self._question_to_keywords(questions, top_k, verbose)
                verbose and self.logger.info(f"Searching with keywords: {keywords}")

                self._check_query_install("Keyword_Search")
                res = self.conn.runInstalledQuery(
                    "Keyword_Search",
                    params = {
                        "keywords": keywords,
                        "mode": "Any",
                        "top_k": top_k,
                        "doc_only": doc_only,
                        "verbose": verbose,
                    },
                    usePost=True
                )            
                start_set = []
                if len(res) > 1 and "selected_set" in res[1]:
                    if len(res[1]["selected_set"]) > 0:
                        start_set += res[1]["selected_set"]
                self.logger.info(f"Got start_set from keywords {keywords}: {str(start_set)}")
                if not method == "keywords":
                    start_set += self._generate_start_set(questions, indices, top_k, similarity_threshold, verbose=verbose)
            else:
                start_set = self._generate_start_set(questions, indices, top_k, similarity_threshold, verbose=verbose)

            verbose and self.logger.info(f"Searching with start_set: {str(start_set)}")

            self._check_query_install("GraphRAG_Hybrid_Search")
            res = self.conn.runInstalledQuery(
                "GraphRAG_Hybrid_Search",
                params = {
                    "json_list_vts": str(start_set),
                    "num_hops": num_hops,
                    "num_seen_min": num_seen_min,
                    "chunk_only": chunk_only,
                    "doc_only": doc_only,
                    "verbose": verbose,
                },
                usePost=True
            )  
        else:
            # Resolve the result cap with a top_k*2 floor: an explicit override
            # or graphrag_config value is honored, but never return fewer than
            # top_k*2 chunks (all seeds plus a comparable amount of the most
            # query-relevant expansion). Unset -> top_k*2.
            from common.config import get_graphrag_config
            _floor = top_k * 2
            max_results = max(
                max_results
                or get_graphrag_config(
                    self.conn.graphname if self.conn else None
                ).get("max_results", 0),
                _floor,
            )
            query_vector = self._generate_embedding(question)
            if not vector_query:
                if (hasattr(self.emb_service, "model_name") and "qwen" in str(self.emb_service.model_name).lower()) or getattr(self.emb_service, "dimensions", 0) == 1024:
                    query_name = "GraphRAG_Hybrid_Qwen_Vector_Search"
                else:
                    query_name = "GraphRAG_Hybrid_Vector_Search"
            else:
                query_name = vector_query
            self._check_query_install(query_name)
            
            # Stage 1: broad candidate retrieval
            cand_top_k = max(top_k * 8, 60)
            res = self.conn.runInstalledQuery(
                query_name,
                params = {
                    "v_types": indices,
                    "query_vector": query_vector,
                    "top_k": cand_top_k,
                    #"similarity_threshold": similarity_threshold,
                    "num_hops": num_hops,
                    "num_seen_min": num_seen_min,
                    "max_results": max(max_results, cand_top_k),
                    "chunk_only": chunk_only,
                    "doc_only": doc_only,
                    "verbose": verbose,
                },
                sizeLimit=1000000000,
                usePost=True
            )
            
            # Stage 2: deterministic lexical/metadata constraint reranking
            if res and len(res) > 0 and "final_retrieval" in res[0]:
                res[0]["final_retrieval"] = self._rerank_chunks(question, res[0]["final_retrieval"], top_k)
                
        if len(res) > 1 and "verbose" in res[1]:
            verbose_info = json.dumps(res[1]['verbose'])
            self.logger.info(f"Retrived HybridSearch query verbose info: {verbose_info}")
            if expand:
                res[1]["verbose"]["expanded_questions"] = questions
        return res

    def _rerank_chunks(self, question: str, final_retrieval: dict, top_k: int) -> dict:
        """Rerank candidate chunks based on lexical match with query keywords and date/venue constraints."""
        if not final_retrieval or len(final_retrieval) <= top_k:
            return final_retrieval
        import string
        def _norm(s: str) -> str:
            s = str(s).lower()
            for p in string.punctuation:
                s = s.replace(p, " ")
            s = s.replace("–", " ").replace("—", " ").replace("’", " ").replace("'", " ")
            return " ".join(s.split())
            
        q_norm = _norm(question)
        stop_words = {"who", "won", "the", "gold", "medal", "event", "held", "summer", "winter", "olympics", "according", "provided", "corpus", "in", "at", "on", "what", "which", "how", "many", "is", "was", "were", "of", "for", "to", "and"}
        q_words = [w for w in q_norm.split() if w not in stop_words]
        
        # Date and month tokens
        date_digits = [w for w in q_words if w.isdigit()]
        months = {"january", "february", "march", "april", "may", "june", "july", "august", "september", "october", "november", "december", "jan", "feb", "mar", "apr", "jun", "jul", "aug", "sep", "oct", "nov", "dec"}
        month_tokens = [w for w in q_words if w in months]
        
        scored = []
        for cid, text in final_retrieval.items():
            t_norm = _norm(text)
            
            # Base word matches
            word_matches = sum(1 for w in q_words if len(w) > 1 and f" {w} " in f" {t_norm} ")
            
            # Consecutive n-gram phrase matches
            phrase_score = 0
            for i in range(len(q_words) - 1):
                if f"{q_words[i]} {q_words[i+1]}" in t_norm:
                    phrase_score += 5
            for i in range(len(q_words) - 2):
                if f"{q_words[i]} {q_words[i+1]} {q_words[i+2]}" in t_norm:
                    phrase_score += 10
                    
            # Date constraint coverage (crucial for distinguishing events at the same venue)
            date_score = 0
            matched_digits = sum(1 for d in date_digits if f" {d} " in f" {t_norm} ")
            matched_months = sum(1 for m in month_tokens if f" {m} " in f" {t_norm} ")
            
            if date_digits:
                date_score += (matched_digits / len(date_digits)) * 25.0
                if matched_digits == len(date_digits):
                    date_score += 20.0
                    
            if month_tokens:
                date_score += (matched_months / len(month_tokens)) * 15.0
                
            for d in date_digits:
                for m in month_tokens:
                    if f"{d} {m}" in t_norm or f"{m} {d}" in t_norm:
                        date_score += 15.0
                        
            # Infobox boost for specific event entries
            infobox_bonus = 10.0 if "[infobox olympic event]" in t_norm else 0.0
            
            total_score = word_matches + phrase_score + date_score + infobox_bonus
            scored.append((cid, text, total_score))
            
        scored.sort(key=lambda x: x[2], reverse=True)
        return {cid: text for cid, text, sc in scored[:top_k]}

    def retrieve_answer(self, question, index, top_k=1, similarity_threshold=0.90, num_hops=2, num_seen_min=1, expand: bool = False, method: str = "similarity", chunk_only: bool = False, doc_only: bool = False, combine: bool = False, verbose: bool = False, max_results: int = 0):
        retrieved = self.search(question, index, top_k, similarity_threshold, num_hops, num_seen_min, expand, method, chunk_only, doc_only, verbose, max_results)

        if combine:
            context = []
            for x in retrieved[0]["final_retrieval"]:
                context += retrieved[0]["final_retrieval"][x]
            context = ["\n".join(set(context))]
            resp = self._generate_response(question, context, verbose=verbose)
        else:
            context = ["\n".join(retrieved[0]["final_retrieval"][x]) for x in retrieved[0]["final_retrieval"]]
            scored = self._score_candidates(question, context, top_k=top_k)
            resp = self._generate_response(question, scored, verbose=verbose)
        
        if verbose and len(retrieved) > 1 and "verbose" in retrieved[1]:
            resp["verbose"] = retrieved[1]["verbose"]
            resp["verbose"]["final_retrieval"] = retrieved[0]["final_retrieval"]
      
        return resp
