// Mapa de navegação da aplicação
export interface NavigationItem {
  id: string;
  name: string;
  path: string;
  parent?: string;
  icon?: string;
  type: 'page' | 'form' | 'report' | 'module';
  keywords?: string[]; // Para melhorar a pesquisa
}

export const navigationMap: NavigationItem[] = [
  // Dashboard
  { id: 'dashboard', name: 'dashboard', path: '/', type: 'page', icon: '🏠' },

  // Master Data
  { id: 'masterdata', name: 'master_data', path: '/masterdata', type: 'module', icon: '📊' },
  { id: 'clients', name: 'clients', path: '/masterdata', parent: 'masterdata', type: 'form', icon: '👤', keywords: ['clientes', 'customers'] },
  { id: 'patients', name: 'patients', path: '/masterdata', parent: 'masterdata', type: 'form', icon: '🏥', keywords: ['pacientes', 'patients'] },
  { id: 'technicians', name: 'technicians', path: '/masterdata', parent: 'masterdata', type: 'form', icon: '👨‍🔧', keywords: ['técnicos', 'technicians'] },
  { id: 'services', name: 'services', path: '/masterdata', parent: 'masterdata', type: 'form', icon: '🔧', keywords: ['serviços', 'services'] },
  { id: 'document_types', name: 'document_types', path: '/masterdata', parent: 'masterdata', type: 'form', icon: '📄', keywords: ['documentos', 'documents'] },
  { id: 'currencies', name: 'currencies', path: '/masterdata', parent: 'masterdata', type: 'form', icon: '💱', keywords: ['moedas', 'currencies'] },
  { id: 'payment_types', name: 'payment_types', path: '/masterdata', parent: 'masterdata', type: 'form', icon: '💳', keywords: ['pagamento', 'payment'] },
  { id: 'payment_forms', name: 'payment_forms', path: '/masterdata', parent: 'masterdata', type: 'form', icon: '💰', keywords: ['pagamento', 'payment'] },
  { id: 'payment_methods', name: 'payment_methods', path: '/masterdata', parent: 'masterdata', type: 'form', icon: '💵', keywords: ['pagamento', 'payment'] },
  { id: 'companies', name: 'companies', path: '/masterdata', parent: 'masterdata', type: 'form', icon: '🏢', keywords: ['empresas', 'laboratórios', 'companies'] },

  // Sales & Marketing
  { id: 'sales', name: 'sales', path: '/sales', type: 'module', icon: '💰' },
  { id: 'sales_orders', name: 'sales_orders', path: '/sales/orders', parent: 'sales', type: 'form', icon: '📋', keywords: ['encomendas', 'orders', 'pedidos'] },
  { id: 'sales_invoices', name: 'sales_invoices', path: '/sales/invoices', parent: 'sales', type: 'form', icon: '🧾', keywords: ['faturas', 'invoices'] },

  // CRM
  { id: 'crm', name: 'crm_module', path: '/crm', type: 'module', icon: '🤝', keywords: ['customer', 'relationship', 'management'] },

  // Production
  { id: 'production', name: 'production', path: '/production', type: 'module', icon: '🏭' },
  { id: 'production_admin', name: 'production_admin', path: '/production/admin', parent: 'production', type: 'page', icon: '⚙️', keywords: ['administração', 'administration'] },
  { id: 'work_centers', name: 'work_centers', path: '/production/workcenters', parent: 'production', type: 'form', icon: '🏗️', keywords: ['centros', 'trabalho', 'work'] },
  { id: 'machine_centers', name: 'machine_centers', path: '/production/machines', parent: 'production', type: 'form', icon: '⚙️', keywords: ['máquinas', 'machines'] },
  { id: 'product_design', name: 'product_design', path: '/production/design', parent: 'production', type: 'page', icon: '🎨', keywords: ['desenho', 'design'] },
  { id: 'capabilities', name: 'capabilities', path: '/production/capabilities', parent: 'production', type: 'page', icon: '⚙️', keywords: ['capacidades', 'capabilities'] },
  { id: 'planning', name: 'planning', path: '/production/planning', parent: 'production', type: 'page', icon: '📅', keywords: ['planeamento', 'planning'] },
  { id: 'execution', name: 'execution', path: '/production/execution', parent: 'production', type: 'page', icon: '🏭', keywords: ['execução', 'execution'] },
  { id: 'costing', name: 'costing', path: '/production/costing', parent: 'production', type: 'page', icon: '💰', keywords: ['custeio', 'costing'] },
  { id: 'tasks', name: 'tasks', path: '/production/tasks', parent: 'production', type: 'page', icon: '✓', keywords: ['tarefas', 'tasks'] },

  // Outros módulos (em desenvolvimento)
  { id: 'financial', name: 'financial_management', path: '/module/financial-management', type: 'module', icon: '💵', keywords: ['financeiro', 'financial'] },
  { id: 'purchasing', name: 'purchasing', path: '/module/purchasing', type: 'module', icon: '🛒', keywords: ['compras', 'purchases'] },
  { id: 'warehouse', name: 'warehouse', path: '/module/warehouse', type: 'module', icon: '📦', keywords: ['armazém', 'warehouse'] },
  { id: 'projects', name: 'projects', path: '/module/projects', type: 'module', icon: '📋', keywords: ['projetos', 'projects'] },
  { id: 'resource_planning', name: 'resource_planning', path: '/module/resource-planning', type: 'module', icon: '📊', keywords: ['recursos', 'planning'] },
  { id: 'service', name: 'service', path: '/module/service', type: 'module', icon: '🔧', keywords: ['serviço', 'service'] },
  { id: 'human_resources', name: 'human_resources', path: '/module/human-resources', type: 'module', icon: '👥', keywords: ['recursos humanos', 'hr'] },
  { id: 'integrations', name: 'integrations', path: '/module/integrations', type: 'module', icon: '🔌', keywords: ['integrações', 'integrations'] },
  { id: 'administration', name: 'administration', path: '/module/administration', type: 'module', icon: '⚙️', keywords: ['administração', 'administration'] },
  { id: 'quality', name: 'quality', path: '/module/quality', type: 'module', icon: '✅', keywords: ['qualidade', 'quality'] },
  { id: 'document_capture', name: 'document_capture', path: '/module/document-capture', type: 'module', icon: '📄', keywords: ['documentos', 'captura', 'capture'] },
];

// Função para construir breadcrumbs a partir de um path
export function getBreadcrumbsForPath(path: string): NavigationItem[] {
  const item = navigationMap.find(i => i.path === path);
  if (!item) return [];

  const breadcrumbs: NavigationItem[] = [];
  let current: NavigationItem | undefined = item;

  while (current) {
    breadcrumbs.unshift(current);
    if (current.parent) {
      current = navigationMap.find(i => i.id === current!.parent);
    } else {
      break;
    }
  }

  return breadcrumbs;
}

// Função para pesquisar itens
export function searchNavigation(query: string, limit = 10): NavigationItem[] {
  if (!query || query.trim().length < 2) return [];

  const lowerQuery = query.toLowerCase().trim();
  const results: Array<{ item: NavigationItem; score: number }> = [];

  for (const item of navigationMap) {
    let score = 0;

    // Buscar no nome (maior peso)
    if (item.name.toLowerCase().includes(lowerQuery)) {
      score += 10;
    }

    // Buscar nas keywords
    if (item.keywords) {
      for (const keyword of item.keywords) {
        if (keyword.toLowerCase().includes(lowerQuery)) {
          score += 5;
        }
      }
    }

    // Buscar no path
    if (item.path.toLowerCase().includes(lowerQuery)) {
      score += 3;
    }

    if (score > 0) {
      results.push({ item, score });
    }
  }

  // Ordenar por score e retornar (usando spread para evitar mutação)
  return [...results]
    .sort((a, b) => b.score - a.score)
    .slice(0, limit)
    .map(r => r.item);
}

// Função para obter o caminho completo (texto) de um item
export function getFullPath(item: NavigationItem): string {
  const breadcrumbs = getBreadcrumbsForPath(item.path);
  return breadcrumbs.map(b => b.name).join(' \\ ');
}
