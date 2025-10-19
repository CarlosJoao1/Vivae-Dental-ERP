import { Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';

export default function Production() {
  const { t } = useTranslation();

  const departments = [
    {
      name: t('product_design'),
      description: t('product_design_desc'),
      icon: '🎨',
      path: '/production/design',
      color: 'bg-purple-50 border-purple-200 hover:bg-purple-100'
    },
    {
      name: t('capabilities'),
      description: t('capabilities_desc'),
      icon: '⚡',
      path: '/production/capabilities',
      color: 'bg-blue-50 border-blue-200 hover:bg-blue-100'
    },
    {
      name: t('planning'),
      description: t('planning_desc'),
      icon: '📅',
      path: '/production/planning',
      color: 'bg-green-50 border-green-200 hover:bg-green-100'
    },
    {
      name: t('execution'),
      description: t('execution_desc'),
      icon: '🔨',
      path: '/production/execution',
      color: 'bg-orange-50 border-orange-200 hover:bg-orange-100'
    },
    {
      name: t('costing'),
      description: t('costing_desc'),
      icon: '💰',
      path: '/production/costing',
      color: 'bg-yellow-50 border-yellow-200 hover:bg-yellow-100'
    },
    {
      name: t('tasks'),
      description: t('tasks_desc'),
      icon: '✅',
      path: '/production/tasks',
      color: 'bg-teal-50 border-teal-200 hover:bg-teal-100'
    }
  ];

  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-xl font-semibold">{t('production')}</h1>
        <p className="text-sm text-gray-600 mt-1">{t('production_departments')}</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {departments.map((dept) => (
          <Link
            key={dept.path}
            to={dept.path}
            className={`block p-4 rounded-lg border-2 ${dept.color} transition-all duration-200`}
          >
            <div className="flex items-center gap-3 mb-2">
              <span className="text-2xl">{dept.icon}</span>
              <div className="flex-1">
                <h3 className="font-semibold text-sm text-gray-800">{dept.name}</h3>
                <p className="text-xs text-gray-600 mt-0.5">{dept.description}</p>
              </div>
            </div>
            <div className="text-xs font-semibold text-blue-600 mt-2 flex items-center gap-1">
              <span>→</span> {t('click_to_access') || 'Clique para aceder'}
            </div>
          </Link>
        ))}
      </div>

      {/* Administration & Master Data */}
      <div className="card p-4">
        <h2 className="text-base font-semibold mb-3">⚙️ {t('administration') || 'Administration'}</h2>
        <div className="flex flex-wrap gap-2">
          <Link to="/production/masterdata" className="px-4 py-2 text-sm bg-blue-100 hover:bg-blue-200 text-blue-800 rounded-lg transition-colors font-medium">
            🗃️ {t('master_data') || 'Master Data'}
          </Link>
          <Link to="/production/admin" className="px-4 py-2 text-sm bg-gray-100 hover:bg-gray-200 rounded-lg transition-colors">
            📋 {t('production_admin')}
          </Link>
          <Link to="/production/workcenters" className="px-4 py-2 text-sm bg-gray-100 hover:bg-gray-200 rounded-lg transition-colors">
            🏭 {t('work_centers')}
          </Link>
          <Link to="/production/machines" className="px-4 py-2 text-sm bg-gray-100 hover:bg-gray-200 rounded-lg transition-colors">
            ⚙️ {t('machine_centers')}
          </Link>
        </div>
      </div>
    </div>
  );
}
