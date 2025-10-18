import { useTranslation } from 'react-i18next';
import { useParams, Link } from 'react-router-dom';

interface ModuleInfo {
  [key: string]: {
    icon: string;
    color: string;
    description: string;
  };
}

const moduleInfo: ModuleInfo = {
  'financial-management': {
    icon: '💰',
    color: 'from-green-400 to-green-600',
    description: 'Complete financial management including accounting, budgets, and reporting'
  },
  'purchasing': {
    icon: '🛒',
    color: 'from-blue-400 to-blue-600',
    description: 'Purchase orders, supplier management, and procurement workflows'
  },
  'warehouse': {
    icon: '📦',
    color: 'from-purple-400 to-purple-600',
    description: 'Inventory management, stock control, and warehouse operations'
  },
  'projects': {
    icon: '📋',
    color: 'from-yellow-400 to-yellow-600',
    description: 'Project planning, tracking, and resource allocation'
  },
  'resource-planning': {
    icon: '📊',
    color: 'from-indigo-400 to-indigo-600',
    description: 'Enterprise resource planning and optimization'
  },
  'service': {
    icon: '🔧',
    color: 'from-red-400 to-red-600',
    description: 'Customer service, support tickets, and maintenance'
  },
  'human-resources': {
    icon: '👥',
    color: 'from-teal-400 to-teal-600',
    description: 'Employee management, payroll, and HR processes'
  },
  'integrations': {
    icon: '🔌',
    color: 'from-pink-400 to-pink-600',
    description: 'API integrations, data sync, and external connections'
  },
  'administration': {
    icon: '⚙️',
    color: 'from-gray-400 to-gray-600',
    description: 'System administration, user management, and configuration'
  },
  'quality': {
    icon: '✅',
    color: 'from-emerald-400 to-emerald-600',
    description: 'Quality control, standards compliance, and auditing'
  },
  'document-capture': {
    icon: '📄',
    color: 'from-cyan-400 to-cyan-600',
    description: 'Document scanning, OCR, and digital archiving'
  }
};

export default function ModuleInDevelopment() {
  const { t } = useTranslation();
  const { moduleId = '' } = useParams<{ moduleId: string }>();
  
  const module = moduleInfo[moduleId];
  const moduleKey = moduleId.replace('-', '_');

  if (!module) {
    return (
      <div className="space-y-6">
        <div className="text-center py-12">
          <h1 className="text-2xl font-semibold text-gray-800">{t('module_not_found', 'Module not found')}</h1>
          <Link to="/" className="text-blue-600 hover:text-blue-800 mt-4 inline-block">
            {t('back_to_dashboard', 'Back to Dashboard')}
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className={`bg-gradient-to-r ${module.color} text-white rounded-lg p-6`}>
        <div className="flex items-center gap-4">
          <span className="text-4xl">{module.icon}</span>
          <div>
            <h1 className="text-3xl font-bold">{t(moduleKey)}</h1>
            <p className="text-white/90 text-lg">{module.description}</p>
          </div>
        </div>
      </div>

      {/* Status Alert */}
      <div className="bg-orange-50 border border-orange-200 rounded-lg p-6">
        <div className="flex items-center gap-3">
          <span className="text-2xl">🚧</span>
          <div>
            <h2 className="text-lg font-semibold text-orange-800">{t('under_development')}</h2>
            <p className="text-orange-700">{t('status_dev_license')}</p>
          </div>
        </div>
      </div>

      {/* Features Preview */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="card">
          <h3 className="text-lg font-semibold mb-3 flex items-center gap-2">
            <span>🎯</span>
            {t('planned_features', 'Planned Features')}
          </h3>
          <ul className="space-y-2 text-gray-600">
            <li className="flex items-center gap-2">
              <span className="w-2 h-2 bg-blue-500 rounded-full"></span>
              {t('feature_admin_panel', 'Administration Panel')}
            </li>
            <li className="flex items-center gap-2">
              <span className="w-2 h-2 bg-blue-500 rounded-full"></span>
              {t('feature_data_management', 'Data Management')}
            </li>
            <li className="flex items-center gap-2">
              <span className="w-2 h-2 bg-blue-500 rounded-full"></span>
              {t('feature_reporting', 'Reporting & Analytics')}
            </li>
            <li className="flex items-center gap-2">
              <span className="w-2 h-2 bg-blue-500 rounded-full"></span>
              {t('feature_integrations', 'Third-party Integrations')}
            </li>
          </ul>
        </div>

        <div className="card">
          <h3 className="text-lg font-semibold mb-3 flex items-center gap-2">
            <span>📋</span>
            {t('licensing_info', 'Licensing Information')}
          </h3>
          <div className="space-y-3 text-gray-600">
            <p>{t('licensing_description', 'This module requires a valid license to access.')}</p>
            <div className="bg-gray-50 p-3 rounded">
              <p className="text-sm font-medium text-gray-800">{t('contact_sales', 'Contact Sales')}</p>
              <p className="text-xs text-gray-600">{t('contact_sales_description', 'Get in touch to learn more about pricing and licensing options.')}</p>
            </div>
          </div>
        </div>
      </div>

      {/* Navigation */}
      <div className="flex justify-between items-center pt-6 border-t">
        <Link 
          to="/" 
          className="text-gray-600 hover:text-gray-800 flex items-center gap-2"
        >
          <span>←</span>
          {t('back_to_dashboard', 'Back to Dashboard')}
        </Link>
        <button 
          className="btn btn-primary"
          onClick={() => alert(t('contact_sales_action', 'Please contact sales for licensing information.'))}
        >
          {t('request_license', 'Request License')}
        </button>
      </div>
    </div>
  );
}