import { Link, useLocation } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { getBreadcrumbsForPath, type NavigationItem } from '@/lib/navigation';

export default function Breadcrumbs() {
  const { t } = useTranslation();
  const location = useLocation();
  
  const breadcrumbs = getBreadcrumbsForPath(location.pathname);

  // Se não houver breadcrumbs ou só tiver o dashboard, não mostrar
  if (breadcrumbs.length === 0 || (breadcrumbs.length === 1 && breadcrumbs[0].id === 'dashboard')) {
    return null;
  }

  return (
    <nav className="flex items-center gap-1.5 text-sm">
      {breadcrumbs.map((item, index) => {
        const isLast = index === breadcrumbs.length - 1;
        
        return (
          <div key={item.id} className="flex items-center gap-1.5">
            {index > 0 && (
              <span className="text-gray-400 dark:text-gray-600">›</span>
            )}
            {isLast ? (
              <span className="font-medium text-gray-900 dark:text-gray-100 flex items-center gap-1.5">
                {item.icon && <span className="text-base">{item.icon}</span>}
                {t(item.name)}
              </span>
            ) : (
              <Link
                to={item.path}
                className="text-gray-600 dark:text-gray-400 hover:text-blue-600 dark:hover:text-blue-400 transition-colors flex items-center gap-1.5"
              >
                {item.icon && <span className="text-base">{item.icon}</span>}
                {t(item.name)}
              </Link>
            )}
          </div>
        );
      })}
    </nav>
  );
}
