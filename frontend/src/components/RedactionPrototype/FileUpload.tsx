import React, { useRef } from 'react';

interface FileUploadProps {
  onFilesUpload: (files: FileList | null) => void;
  loading: boolean;
}

const FileUpload: React.FC<FileUploadProps> = ({ onFilesUpload, loading }) => {
  const fileInput = useRef<HTMLInputElement>(null);

  return (
    <div className="file-upload">
      <button
        onClick={() => fileInput.current?.click()}
        className="upload-button"
        disabled={loading}
      >
        {loading ? 'Загрузка...' : 'Загрузить изображения'}
      </button>
      <input
        type="file"
        ref={fileInput}
        multiple
        className="file-input"
        onChange={e => onFilesUpload(e.target.files)}
        accept="image/*"
      />
    </div>
  );
};

export default FileUpload;