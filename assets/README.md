# VIVAE ERP - Assets

Esta pasta contém todos os recursos visuais do projeto VIVAE ERP.

## Estrutura de Pastas

### `/logos`
- Logo principal do VIVAE ERP
- Variações (horizontal, vertical, monocromático)
- Formatos: SVG, PNG (diferentes tamanhos), ICO

### `/images`
- Imagens promocionais
- Screenshots da aplicação
- Banners e headers
- Ícones personalizados

## Padrões de Nomenclatura

### Logos
- `vivae-erp-logo-main.svg` - Logo principal vetorial
- `vivae-erp-logo-main-{size}.png` - Logo principal em PNG (sizes: 32, 64, 128, 256, 512)
- `vivae-erp-logo-horizontal.svg` - Logo horizontal
- `vivae-erp-logo-mono.svg` - Logo monocromático
- `favicon.ico` - Favicon para navegadores

### Imagens
- `vivae-erp-banner-{context}.png` - Banners (context: hero, header, social)
- `vivae-erp-screenshot-{page}.png` - Screenshots das páginas
- `vivae-erp-icon-{element}.svg` - Ícones específicos

## Cores do Projeto

### Palette Principal
- **Azul Principal**: #3B82F6 (blue-500)
- **Azul Escuro**: #1E40AF (blue-800)
- **Azul Claro**: #DBEAFE (blue-100)
- **Branco**: #FFFFFF
- **Cinza**: #6B7280 (gray-500)

### Uso das Cores
- Azul Principal: Elementos interativos, botões primários
- Azul Escuro: Texto de destaque, headers
- Azul Claro: Backgrounds suaves, estados hover
- Branco: Background principal, texto em elementos escuros
- Cinza: Texto secundário, borders

## Diretrizes de Uso

1. **Logo Principal**: Usar em headers, login, splash screens
2. **Logo Horizontal**: Melhor para sidebars e footers
3. **Logo Monocromático**: Para documentos impressos ou fundos coloridos
4. **Favicon**: Gerar em múltiplos tamanhos (16x16, 32x32, 48x48)

## Como Adicionar Novos Assets

1. Colocar o arquivo na pasta apropriada
2. Seguir a convenção de nomenclatura
3. Adicionar referência neste README
4. Atualizar as referências no código se necessário

## Integração no Frontend

Os assets devem ser copiados para `frontend/public/assets/` durante o build para serem acessíveis via URL pública.