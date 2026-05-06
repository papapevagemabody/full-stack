import React from 'react';
import { FileData } from '../../types';

interface ImageGalleryProps {
  files: FileData[];
  selected: FileData | null;
  onSelect: (file: FileData) => void;
}

const ImageGallery: React.FC<ImageGalleryProps> = ({ files, selected, onSelect }) => {
  return (
    <div className="image-gallery">
      <h3>Галерея изображений</h3>
      <div className="gallery-grid">
        {files.map(file => (
          <img
            key={file.id}
            src={file.url}
            alt={file.name ? `Миниатюра в галерее: ${file.name}` : 'Изображение в галерее'}
            className={`gallery-image ${selected?.id === file.id ? 'selected' : ''}`}
            loading="lazy"
            decoding="async"
            onClick={() => onSelect(file)}
          />
        ))}
      </div>
    </div>
  );
};

export default ImageGallery;