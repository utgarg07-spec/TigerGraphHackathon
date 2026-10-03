import { useState, ReactElement } from "react";
import { ConfirmDialog } from "@/components/ui/confirm-dialog";

interface ConfirmOptions {
  message: string;
  onConfirm: () => void;
  onCancel: () => void;
}

export function useConfirm(): [
  (message: string) => Promise<boolean>,
  ReactElement | null,
  boolean
] {
  const [options, setOptions] = useState<ConfirmOptions | null>(null);

  const confirm = (message: string): Promise<boolean> =>
    new Promise<boolean>((resolve) => {
      setOptions({
        message,
        onConfirm: () => {
          resolve(true);
          setOptions(null);
        },
        onCancel: () => {
          resolve(false);
          setOptions(null);
        },
      });
    });

  const confirmDialog: ReactElement | null = options ? (
    <ConfirmDialog
      message={options.message}
      onConfirm={options.onConfirm}
      onCancel={options.onCancel}
    />
  ) : null;

  const isOpen = options !== null;

  return [confirm, confirmDialog, isOpen];
}

