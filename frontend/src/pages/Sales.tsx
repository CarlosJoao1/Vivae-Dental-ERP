import { Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';

export default function Sales() {
  const { t } = useTranslation();

  const salesModules = [
    {
      name: t('sales_orders'),
      description: t('orders_invoices'),
      icon: '📋',
      path: '/sales/orders',
      color: 'bg-blue-50 border-blue-200 hover:bg-blue-100'
    },
    {
      name: t('sales_invoices'),
      description: t('orders_invoices'),
      icon: '🧾',
      path: '/sales/invoices',
      color: 'bg-green-50 border-green-200 hover:bg-green-100'
    }
  ];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold">{t('sales_module')}</h1>
        <p className="text-gray-600 mt-1">{t('orders_invoices')}</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {salesModules.map((module) => (
          <Link
            key={module.path}
            to={module.path}
            className={`block p-6 rounded-lg border-2 ${module.color} transition-all duration-200`}
          >
            <div className="flex items-center gap-3 mb-3">
              <span className="text-3xl">{module.icon}</span>
              <h3 className="font-semibold text-lg text-gray-800">{module.name}</h3>
            </div>
            <p className="text-sm text-gray-600">{module.description}</p>
          </Link>
        ))}
      </div>
    </div>
  );
}
