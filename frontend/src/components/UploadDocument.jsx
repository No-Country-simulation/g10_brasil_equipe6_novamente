
import { useRef, useState } from "react";

function UploadDocument({ onFileSelect }) {
  const [file, setFile] = useState(null);
  const [isDragging, setIsDragging] = useState(false);
  const inputRef = useRef(null);

  const handleFile = (selectedFile) => {
    if (!selectedFile) return;

    const allowedTypes = [".pdf", ".md", ".txt"];
    const extension = selectedFile.name
      .slice(selectedFile.name.lastIndexOf("."))
      .toLowerCase();

    if (!allowedTypes.includes(extension)) {
      alert("Formato inválido! Envie PDF, MD ou TXT.");
      return;
    }

    setFile(selectedFile);
    onFileSelect(selectedFile);
  };

  const handleDrop = (event) => {
    event.preventDefault();
    setIsDragging(false);
    handleFile(event.dataTransfer.files[0]);
  };

  const handleRemove = () => {
    setFile(null);
    onFileSelect(null);
    inputRef.current.value = "";
  };

  return (
    <section className="w-full space-y-3">
      <div>
        <h2 className="text-lg font-semibold text-white">
          1. Envie o Documento Original
        </h2>

        <p className="mt-2 text-sm text-gray-400">
          Formatos suportados: PDF, MD, TXT
        </p>
      </div>

      <div
        onDragOver={(event) => {
          event.preventDefault();
          setIsDragging(true);
        }}
        onDragLeave={() => setIsDragging(false)}
        onDrop={handleDrop}
        onClick={() => inputRef.current.click()}
        className={`flex cursor-pointer items-center gap-4 rounded-lg border p-5 transition ${
          isDragging
            ? "border-pink-400 bg-pink-500/10"
            : "border-gray-700 bg-zinc-800 hover:border-pink-400"
        }`}
      >
        <input
          ref={inputRef}
          type="file"
          accept=".pdf,.md,.txt"
          className="hidden"
          onChange={(event) => handleFile(event.target.files[0])}
        />

        <div className="rounded-md bg-zinc-700 px-4 py-2 text-sm text-white">
          ↑ Upload
        </div>

        <div className="text-sm text-gray-400">
          {file ? (
            <span className="text-green-400">{file.name}</span>
          ) : (
            "Arraste seu arquivo ou clique para selecionar"
          )}
        </div>
      </div>

      {file && (
        <button
          type="button"
          onClick={handleRemove}
          className="text-sm text-red-400 hover:text-red-300"
        >
          Remover arquivo
        </button>
      )}
    </section>
  );
}

export default UploadDocument;
