import {useEffect, useRef, useState} from 'react';
import {
  Table,
  TableBody,
  TableCaption,
  TableCell,
  TableFooter,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"

import {
  Pagination,
  PaginationContent,
  PaginationItem,
  PaginationNext,
  PaginationPrevious,
} from "@/components/ui/pagination"

interface Post {
  id: number;
  body: string;
}

export const KnowledgeTablPro = ({ data }) => {
  const [theme, setTheme] = useState(localStorage.getItem("vite-ui-theme"));
  const ref = useRef<any | null>(null);
  const [edges, setEdges] = useState<any[]>([]);
  const [dataArray, setdataArray] = useState<any>();
  const [vId, setvId] = useState<any>();
  const [tableData, setTableData] = useState<any[]>([]);
  const [columns, setColumns] = useState<string[]>([]);
  const [dataType, setDataType] = useState<string>(''); // 'gsql' or 'cypher'

  const rowsPerPage = 10;
  // const [sdata, setData] = useState<Post[]>([]);
  const [startIndex, setStartIndex] = useState(0);
  const [endIndex, setEndIndex] = useState(rowsPerPage);


  // const getData = async () => {
  //   try {
  //     const response = await axios.get('https://jsonplaceholder.typicode.com/posts');
  //     const data = response.data;
  //     console.log(38, data);
  //     setData(data);
  //   } catch (error) {
  //     console.error('Error fetching data:', error);
  //   }
  // }
  // useEffect(() => {
  //   getData();
  // }, [])



  useEffect(() => {
    if (!data) {
      setTableData([]);
      setColumns([]);
      setDataType('');
      setEdges([]);
      return;
    }

    // Handle string data - display it directly
    if (typeof data === 'string') {
      setDataType('gsql');
      setTableData([{ content: data }]);
      setColumns(['content']);
      setEdges([]);
      return;
    }

    // Handle Cypher query results (answer field) - these are objects with data arrays
    if (typeof data === 'object' && !Array.isArray(data)) {
      // Check if this is final_retrieval data structure (SupportAI format)
      if (data.final_retrieval && typeof data.final_retrieval === 'object') {
        setDataType('final_retrieval');
        setEdges([]);

        // Convert final_retrieval structure to table rows
        // Format: {chunk1: [text1, text2, ...], chunk2: [text3, text4, ...]}
        // One row per chunk with all texts combined
        const tableRows: any[] = [];
        const finalRetrieval = data.final_retrieval;

        Object.keys(finalRetrieval).forEach((chunkKey) => {
          const texts = finalRetrieval[chunkKey];
          if (Array.isArray(texts)) {
            // Combine all texts for this chunk into a single string
            const combinedText = texts.join('\n\n');
            tableRows.push({
              chunk: chunkKey,
              text: combinedText
            });
          } else if (typeof texts === 'string') {
            // Handle case where value is a single string instead of array
            tableRows.push({
              chunk: chunkKey,
              text: texts
            });
          }
        });

        if (tableRows.length > 0) {
          setColumns(['chunk', 'text']);
          setTableData(tableRows);
        } else {
          setColumns([]);
          setTableData([]);
        }
        return; // Exit early for final_retrieval data
      }

      // Check if this is Cypher data (object with array values like {"T": [...]} or object values like {"T": {...}})
      const dictKeys = Object.keys(data);
      if (dictKeys.length > 0) {
        const firstKey = dictKeys[0];
        const firstValue = data[firstKey];
        if (Array.isArray(firstValue)) {
          setDataType('cypher');
          setEdges([]); // Clear GSQL edges for Cypher data
          
          if (firstValue.length > 0) {
            // Extract column names from the first row
            const firstRow = firstValue[0];
            const cols = Object.keys(firstRow);
            setColumns(cols);
            setTableData(firstValue);
          } else {
            setColumns([]);
            setTableData([]);
          }
          return; // Exit early for Cypher data
        } else if (firstValue && typeof firstValue === 'object' && !Array.isArray(firstValue)) {
          // Handle object values like {"T": {"entity_type_count": 1036}}
          // Convert to table with Key and Value columns
          setDataType('cypher');
          setEdges([]); // Clear GSQL edges for Cypher data

          const tableRows = Object.keys(firstValue).map(key => ({
            Key: key,
            Value: firstValue[key]
          }));

          if (tableRows.length > 0) {
            setColumns(['Key', 'Value']);
            setTableData(tableRows);
          } else {
            setColumns([]);
            setTableData([]);
          }
          return; // Exit early for Cypher data
        }
      }

      // Handle GSQL results (object with @@edges)
      setDataType('gsql');
      setTableData([]);
      setColumns([]);
      setEdges([]);

      // Look for @@edges in the data
      let setresults: any[] | null = null;

      // Check if data is an array and look for @@edges in each item
      if (Array.isArray(data)) {
        for (const item of data) {
          if (item && typeof item === 'object' && item['@@edges']) {
            setresults = item['@@edges'];
            break;
          }
        }
      } else if (data['@@edges']) {
        // Direct @@edges in the object
        setresults = data['@@edges'];
      }

      if (setresults && Array.isArray(setresults)) {
        setEdges(setresults);
        
        // Extract columns from the first edge if available
        if (setresults.length > 0 && setresults[0]) {
          const firstEdge = setresults[0];
          const cols = Object.keys(firstEdge);
          setColumns(cols);
          setTableData(setresults);
        }
      } else {
        // No @@edges found, try to use the data directly as table data
        if (Array.isArray(data)) {
          if (data.length > 0) {
            const firstItem = data[0];
            const cols = Object.keys(firstItem);
            setColumns(cols);
            setTableData(data);
          }
        }
      }
    }
  }, [data]);

  // useEffect(() => {
  //   setvId(sdata[0]?.rlt[0]?.v_id);
  //   if (typeof sdata === 'object') {
  //     if (sdata.length > 1) {
  //       const setresults = sdata[1]["@@edges"];
  //       console.log('setresults', setresults)
  //       setEdges(setresults);
  //       setdataArray({
  //         "nodes": getNodes
  //       })
  //     } else null
  //   }
  // }, [data, sdata, edges]);

  // const getNodes = edges.map((d:any) => (
  //   {
  //     "directed": `${d.directed}`,
  //     "e_type": `${d.e_type}`,
  //     "from_id": `${d.from_id}`,
  //     "from_type": `${d.from_type}`,
  //     "to_id": `${d.to_id}`,
  //     "to_type": `${d.to_type}`,
  //   }
  // ));

 return (
  <>
      {dataType === 'final_retrieval' && tableData.length > 0 ? (
        <>
          <Table className="text-[11px]">
            <TableHeader>
              <TableRow>
                <TableHead className="w-[100px] text-[11px]">Chunk</TableHead>
                <TableHead className="text-[11px]">Text</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {tableData.slice(startIndex, endIndex).map((item: any, index: number) => (
                <TableRow key={index}>
                  <TableCell className="text-left text-[11px]">{item.chunk}</TableCell>
                  <TableCell className="text-left text-[11px] whitespace-pre-wrap">{item.text}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
          {tableData.length > rowsPerPage && (
            <Pagination className="text-[11px]">
              <PaginationContent>
                <PaginationItem>
                  <PaginationPrevious
                    className={
                      startIndex === 0 ? "pointer-events-none opacity-50" : undefined
                    }
                    onClick={() => {
                      setStartIndex(startIndex - rowsPerPage);
                      setEndIndex(endIndex - rowsPerPage);
                    }} />
                </PaginationItem>

                <PaginationItem>
                  <PaginationNext
                    className={
                      endIndex >= tableData.length ? "pointer-events-none opacity-50" : undefined
                    }
                    onClick={() => {
                      setStartIndex(startIndex + rowsPerPage);
                      setEndIndex(endIndex + rowsPerPage);
                    }} />
                </PaginationItem>
              </PaginationContent>
            </Pagination>
          )}
        </>
      ) : dataType === 'gsql' && tableData.length > 0 && edges.length === 0 ? (
        <>
          <Table className="text-[11px]">
            <TableHeader>
              <TableRow>
                <TableHead className="w-[100px] text-[11px]">Content</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              <TableRow>
                <TableCell className="text-left text-[11px] whitespace-pre-wrap">
                  {tableData[0].content}
                </TableCell>
              </TableRow>
            </TableBody>
          </Table>
        </>
      ) : dataType === 'cypher' && tableData.length > 0 ? (
        <>
          <Table className="text-[11px]">
        <TableHeader>
          <TableRow>
                {columns.map((column) => (
                  <TableHead key={column} className="w-[100px] text-[11px]">
                    {column}
                  </TableHead>
                ))}
          </TableRow>
        </TableHeader>
        <TableBody>
              {tableData.slice(startIndex, endIndex).map((item: any, index: number) => (
                <TableRow key={index}>
                  {columns.map((column) => (
                    <TableCell key={column} className="text-left text-[11px]">
                      {typeof item[column] === 'object' ? 
                        JSON.stringify(item[column]) : 
                        String(item[column] || '')
                      }
                    </TableCell>
                  ))}
                </TableRow>
              ))}
            </TableBody>
          </Table>
          {tableData.length > rowsPerPage && (
            <Pagination className="text-[11px]">
              <PaginationContent>
                <PaginationItem>
                  <PaginationPrevious
                    className={
                      startIndex === 0 ? "pointer-events-none opacity-50" : undefined
                    }
                    onClick={() => {
                      setStartIndex(startIndex - rowsPerPage);
                      setEndIndex(endIndex - rowsPerPage);
                    }} />
                </PaginationItem>

                <PaginationItem>
                  <PaginationNext
                    className={
                      endIndex >= tableData.length ? "pointer-events-none opacity-50" : undefined
                    }
                    onClick={() => {
                      setStartIndex(startIndex + rowsPerPage);
                      setEndIndex(endIndex + rowsPerPage);
                    }} />
                </PaginationItem>
              </PaginationContent>
            </Pagination>
          )}
        </>
      ) : dataType === 'gsql' && edges.length > 0 ? (
        <>
          <Table className="text-[11px]">
            <TableHeader>
              <TableRow>
                <TableHead className="w-[100px] text-[11px]">e_type</TableHead>
                <TableHead className="text-[11px]">from_id</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {edges.slice(startIndex, endIndex).map((item: any, index: number) => (
                <TableRow key={index}>
                  <TableCell className="text-left text-[11px]">{item.e_type}</TableCell>
                  <TableCell className="text-left text-[11px]">{item.from_id}</TableCell>
                </TableRow>
              ))}
        </TableBody>
      </Table>
          {edges.length > rowsPerPage && (
            <Pagination className="text-[11px]">
        <PaginationContent>
          <PaginationItem>
            <PaginationPrevious
              className={
                startIndex === 0 ? "pointer-events-none opacity-50" : undefined
              }
              onClick={() => {
                setStartIndex(startIndex - rowsPerPage);
                setEndIndex(endIndex - rowsPerPage);
              }} />
          </PaginationItem>

          <PaginationItem>
            <PaginationNext
              className={
                      endIndex >= edges.length ? "pointer-events-none opacity-50" : undefined
              }
              onClick={() => {
                      setStartIndex(startIndex + rowsPerPage);
                      setEndIndex(endIndex + rowsPerPage);
              }} />
          </PaginationItem>
        </PaginationContent>
      </Pagination>
          )}
        </>
      ) : (
        <div className="text-center py-8 text-gray-500 text-[11px]">
          No data available to display in table format
        </div>
      )}


    {/* {typeof data} */}
    {/* {typeof sdata !== 'number' && typeof sdata !== 'string' && dataArray?.nodes ? (
      <>
        <Tabs defaultValue="v_" className="w-[100%] text-sm lg:text-lg">
          <TabsList className="w-[100%]">
            <TabsTrigger value="v_">v_</TabsTrigger>
            <TabsTrigger value="@@edges">@@edges</TabsTrigger>
          </TabsList>
          <TabsContent value="v_">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>v_id</TableHead>
                  <TableHead>v_type</TableHead>
                  <TableHead >rlt.@count"</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                  <TableRow key='0'>
                    <TableCell>{sdata[0]?.rlt[0]?.v_id}</TableCell>
                    <TableCell>{sdata[0]?.rlt[0]?.v_type}</TableCell>
                    <TableCell>{sdata[0]?.rlt[0]?.attributes["rlt.@count"]}</TableCell>
                  </TableRow>
              </TableBody>
            </Table>
          </TabsContent>
          <TabsContent value="@@edges">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="w-[100px]">directed</TableHead>
                  <TableHead>e_type</TableHead>
                  <TableHead >from_id</TableHead>
                  <TableHead >from_type</TableHead>
                  <TableHead >to_id</TableHead>
                  <TableHead >to_type</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {dataArray?.nodes?.map((d:any) => (
                  <TableRow key='0'>
                    <TableCell>{d.directed}</TableCell>
                    <TableCell>{d.e_type}</TableCell>
                    <TableCell>{d.from_id}</TableCell>
                    <TableCell>{d.from_type}</TableCell>
                    <TableCell>{d.to_id}</TableCell>
                    <TableCell>{d.to_type}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TabsContent>
        </Tabs>
      </>
    ) : <div className='m-10'>Sorry no graph or table available</div> } */}
  </>
 )
}












// function App() {
//   const rowsPerPage = 10;
//   const [data, setData] = useState<Post[]>([]);
//   const [startIndex, setStartIndex] = useState(0);
//   const [endIndex, setEndIndex] = useState(rowsPerPage);


//   const getData = async () => {
//     try {
//       const response = await axios.get('https://jsonplaceholder.typicode.com/posts');
//       const data = response.data;
//       console.log(38, data);
//       setData(data);
//     } catch (error) {
//       console.error('Error fetching data:', error);
//     }
//   }
//   useEffect(() => {
//     getData();
//   }, [])

//   return (
//     <>
//       <Table>
//         <TableHeader>
//           <TableRow>
//             <TableHead className="w-[100px]">Id</TableHead>
//             <TableHead>Body</TableHead>
//           </TableRow>
//         </TableHeader>
//         <TableBody>
//           {data.slice(startIndex, endIndex).map((item) => {
//             return <>
//               <TableRow>
//                 <TableCell className="text-left">{item.id}</TableCell>
//                 <TableCell className="text-left">{item.body}</TableCell>
//               </TableRow>
//             </>
//           })}

//         </TableBody>
//       </Table>
//       <Pagination>
//         <PaginationContent>
//           <PaginationItem>
//             <PaginationPrevious
//               className={
//                 startIndex === 0 ? "pointer-events-none opacity-50" : undefined
//               }
//               onClick={() => {
//                 setStartIndex(startIndex - rowsPerPage);
//                 setEndIndex(endIndex - rowsPerPage);
//               }} />
//           </PaginationItem>

//           <PaginationItem>
//             <PaginationNext
//               className={
//                 endIndex === 100 ? "pointer-events-none opacity-50" : undefined
//               }
//               onClick={() => {
//                 setStartIndex(startIndex + rowsPerPage); //10
//                 setEndIndex(endIndex + rowsPerPage); //10 + 10 = 20
//               }} />
//           </PaginationItem>
//         </PaginationContent>
//       </Pagination>

//     </>
//   )
// }

// export default App
