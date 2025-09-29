// src/pages/ModulePlaceholder.tsx
import React, { PropsWithChildren } from "react";

type ModulePlaceholderProps = PropsWithChildren<{
  title?: string;
  description?: string;
}>;

const ModulePlaceholder: React.FC<ModulePlaceholderProps> = ({
  title,
  description,
  children,
}) => {
  return (
    <div className="p-6">
      {title && <h2 className="text-xl font-semibold">{title}</h2>}
      {description && <p className="text-gray-600 mt-1">{description}</p>}
      {children && <div className="mt-4">{children}</div>}
    </div>
  );
};

export default ModulePlaceholder;
