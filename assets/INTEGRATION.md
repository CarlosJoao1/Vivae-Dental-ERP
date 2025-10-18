# Favicon Integration for VIVAE ERP

## Current Status
- Placeholder favicon needed
- Integration points prepared

## Integration Points

### 1. HTML Head (frontend/index.html)
```html
<link rel="icon" type="image/x-icon" href="/assets/favicon.ico">
<link rel="icon" type="image/png" sizes="32x32" href="/assets/favicon-32x32.png">
<link rel="icon" type="image/png" sizes="16x16" href="/assets/favicon-16x16.png">
<link rel="apple-touch-icon" sizes="180x180" href="/assets/apple-touch-icon.png">
```

### 2. Vite Configuration (vite.config.ts)
```typescript
// Add to vite config for asset handling
export default defineConfig({
  // ... existing config
  publicDir: 'public',
  assetsInclude: ['**/*.ico', '**/*.png', '**/*.svg']
})
```

### 3. Component Integration
```tsx
// For logo in components
import logoSvg from '/assets/vivae-erp-logo-main.svg'

const Logo = () => (
  <img src={logoSvg} alt="VIVAE ERP" className="h-8 w-auto" />
)
```

## TODO
1. Generate logo/favicon with OpenAI
2. Place files in assets/logos/
3. Copy to frontend/public/assets/
4. Update HTML references
5. Update component imports