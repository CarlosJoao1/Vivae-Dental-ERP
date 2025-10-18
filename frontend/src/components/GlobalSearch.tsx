import { useState, useRef, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { searchNavigation, getFullPath, type NavigationItem } from '@/lib/navigation';

export default function GlobalSearch() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<NavigationItem[]>([]);
  const [isOpen, setIsOpen] = useState(false);
  const [selectedIndex, setSelectedIndex] = useState(0);
  const inputRef = useRef<HTMLInputElement>(null);
  const dropdownRef = useRef<HTMLDivElement>(null);

  // Pesquisar quando o query muda
  useEffect(() => {
    if (query.trim().length >= 2) {
      const searchResults = searchNavigation(query, 8);
      setResults(searchResults);
      setIsOpen(searchResults.length > 0);
      setSelectedIndex(0);
    } else {
      setResults([]);
      setIsOpen(false);
    }
  }, [query]);

  // Fechar dropdown quando clicar fora
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (
        dropdownRef.current &&
        !dropdownRef.current.contains(event.target as Node) &&
        inputRef.current &&
        !inputRef.current.contains(event.target as Node)
      ) {
        setIsOpen(false);
      }
    }

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // Navegação por teclado
  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (!isOpen || results.length === 0) return;

    switch (e.key) {
      case 'ArrowDown':
        e.preventDefault();
        setSelectedIndex(prev => (prev + 1) % results.length);
        break;
      case 'ArrowUp':
        e.preventDefault();
        setSelectedIndex(prev => (prev - 1 + results.length) % results.length);
        break;
      case 'Enter':
        e.preventDefault();
        if (results[selectedIndex]) {
          navigateToItem(results[selectedIndex]);
        }
        break;
      case 'Escape':
        setIsOpen(false);
        inputRef.current?.blur();
        break;
    }
  };

  // Navegar para um item
  const navigateToItem = (item: NavigationItem) => {
    navigate(item.path);
    setQuery('');
    setIsOpen(false);
    inputRef.current?.blur();
  };

  // Obter ícone do tipo
  const getTypeIcon = (type: string) => {
    switch (type) {
      case 'page': return '📄';
      case 'form': return '📝';
      case 'report': return '📊';
      case 'module': return '📦';
      default: return '📌';
    }
  };

  return (
    <div className="relative">
      <input
        ref={inputRef}
        type="text"
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        onKeyDown={handleKeyDown}
        onFocus={() => {
          if (query.trim().length >= 2 && results.length > 0) {
            setIsOpen(true);
          }
        }}
        placeholder={t('search') as string}
        className="px-3 py-2 rounded border dark:border-gray-700 bg-white dark:bg-gray-800 min-w-[240px] text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
      />

      {/* Dropdown de resultados */}
      {isOpen && results.length > 0 && (
        <div
          ref={dropdownRef}
          className="absolute top-full left-0 mt-1 w-[400px] bg-white dark:bg-gray-800 border dark:border-gray-700 rounded-lg shadow-xl z-50 max-h-[400px] overflow-y-auto"
        >
          <div className="p-2">
            <div className="text-xs text-gray-500 dark:text-gray-400 mb-2 px-2">
              {results.length} {results.length === 1 ? 'resultado' : 'resultados'}
            </div>
            {results.map((item, index) => (
              <button
                key={item.id}
                onClick={() => navigateToItem(item)}
                className={`w-full text-left px-3 py-2 rounded-md transition-colors ${
                  index === selectedIndex
                    ? 'bg-blue-50 dark:bg-blue-900/30 border border-blue-200 dark:border-blue-700'
                    : 'hover:bg-gray-50 dark:hover:bg-gray-700'
                }`}
              >
                <div className="flex items-start gap-2">
                  <span className="text-lg mt-0.5 flex-shrink-0">
                    {item.icon || getTypeIcon(item.type)}
                  </span>
                  <div className="flex-1 min-w-0">
                    <div className="font-medium text-sm text-gray-900 dark:text-gray-100 truncate">
                      {t(item.name)}
                    </div>
                    <div className="text-xs text-gray-500 dark:text-gray-400 mt-0.5 flex items-center gap-2">
                      <span className="truncate">{getFullPath(item).split(' \\ ').map(p => t(p)).join(' › ')}</span>
                      <span className="flex-shrink-0 px-1.5 py-0.5 rounded text-[10px] bg-gray-100 dark:bg-gray-700 uppercase">
                        {t(item.type)}
                      </span>
                    </div>
                  </div>
                </div>
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Hint quando estiver vazio */}
      {query.trim().length > 0 && query.trim().length < 2 && (
        <div className="absolute top-full left-0 mt-1 w-[240px] bg-white dark:bg-gray-800 border dark:border-gray-700 rounded-lg shadow-md z-50 p-2">
          <div className="text-xs text-gray-500 dark:text-gray-400 text-center">
            Digite pelo menos 2 caracteres...
          </div>
        </div>
      )}
    </div>
  );
}
