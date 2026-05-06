import React from 'react';
import { FileData } from '../../types';

interface ImageViewerProps {
  file: FileData;
}

const ImageViewer: React.FC<ImageViewerProps> = ({ file }) => {
  return (
    <div className="image-viewer">
      <h3>Просмотр: {file.name}</h3>
      <div className="viewer-container">
        <img
          src={file.url}
          alt={file.name ? `Просмотр с разметкой лиц: ${file.name}` : 'Просмотр изображения'}
          className="viewer-image"
          loading="lazy"
          decoding="async"
        />
        {file.detections.map((detection, index) => {
          const [x, y, width, height] = detection.bbox;
          return (
            <div
              key={index}
              className="detection-box"
              style={{
                left: `${x * 100}%`,
                top: `${y * 100}%`,
                width: `${width * 100}%`,
                height: `${height * 100}%`
              }}
            />
          );
        })}
      </div>
    </div>
  );
};

export default ImageViewer;