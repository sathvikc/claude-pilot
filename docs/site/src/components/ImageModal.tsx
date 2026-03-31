import { useState } from "react";
import { Dialog, DialogContent } from "@/components/ui/dialog";

interface ImageModalProps {
  src: string;
  fallback?: string;
  alt: string;
  className?: string;
}

const ImageModal = ({ src, fallback, alt, className = "" }: ImageModalProps) => {
  const [isOpen, setIsOpen] = useState(false);

  const renderImage = (imgClassName: string, onClick: () => void) => {
    if (fallback) {
      return (
        <picture>
          <source srcSet={src} type="image/webp" />
          <img
            src={fallback}
            alt={alt}
            className={imgClassName}
            onClick={onClick}
            loading="lazy"
          />
        </picture>
      );
    }
    return (
      <img
        src={src}
        alt={alt}
        className={imgClassName}
        onClick={onClick}
        loading="lazy"
      />
    );
  };

  return (
    <>
      {renderImage(
        `cursor-pointer hover:opacity-90 transition-opacity ${className}`,
        () => setIsOpen(true),
      )}
      <Dialog open={isOpen} onOpenChange={setIsOpen}>
        <DialogContent className="max-w-[95vw] max-h-[95vh] p-0 border-0 bg-transparent">
          {renderImage(
            "w-full h-full object-contain rounded-lg",
            () => setIsOpen(false),
          )}
        </DialogContent>
      </Dialog>
    </>
  );
};

export default ImageModal;
