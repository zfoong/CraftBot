# Model Configuration Provider Dropdown Fix

## Problem
The Provider dropdown in the Model Configuration settings was stuck on "Anthropic" and couldn't be changed to other providers like OpenAI, Gemini, or BytePlus.

## Root Cause
The React component had a **circular dependency** in its `useEffect` hook:
- When you changed the provider from "Anthropic" to another option
- The effect would re-run and fetch the OLD settings from the server
- This would immediately reset the provider back to what was saved (Anthropic)
- Creating a loop where changes were impossible

## Solution Applied

### Fix 1: Split useEffect into Two Effects
**File:** `app/ui_layer/browser/frontend/src/pages/Settings/SettingsPage.tsx`

- **Effect 1:** Sets up message handlers (runs once when connected)
  - Removed problematic dependencies that caused re-fetching
  - Only initializes on first load
  
- **Effect 2:** Loads initial data (runs once on mount)
  - Only fetches provider and settings when first connected
  - No longer re-fetches when local state changes

### Fix 2: Improved Reset Button
- Removed `hasInitialized.current = false` which would cause unwanted re-fetching
- Added success toast notification for better UX
- Ensures clean reset to Anthropic provider

## How to Apply the Fix

### 1. **Build the Frontend**
```powershell
# Navigate to the frontend directory
cd app/ui_layer/browser/frontend

# Install dependencies (if not already done)
npm install

# Build the optimized production bundle
npm run build

# Or for development with hot reload:
npm run dev
```

### 2. **Clear Cache** (if needed)
Stop the CraftBot app and clear browser cache:
- Press `Ctrl+Shift+Delete` in browser
- Clear cache for localhost:3000 or your app URL

### 3. **Restart CraftBot**
```powershell
python run.py
```

or for TUI mode:
```powershell
python run.py --tui
```

## Testing the Fix

Once restarted, test these scenarios in Settings → Model:

✅ **Provider Selection:**
- Click the Provider dropdown
- You should be able to select: OpenAI, Anthropic, Google Gemini, BytePlus, or Local (Ollama)
- Selection should stick (not reset immediately)

✅ **Saving Changes:**
- Change provider to a different one
- Configure the LLM/VLM models
- Click Save button
- Changes should persist after page refresh

✅ **Reset Configuration:**
- Change to any provider
- Click "Reset Configuration" button
- Should reset to Anthropic with success message
- All settings cleared

## What Changed in Code

### Before (Broken):
```typescript
const [provider, setProvider] = useState('anthropic')

useEffect(() => {
  if (!isConnected) return
  
  onMessage('model_settings_get', (data) => {
    // This overwrites provider state!
    setProvider(data.llm_provider)
  })
  
  send('model_settings_get')
  
  // ❌ PROBLEM: provider in dependency array causes re-fetch
  return () => cleanups.forEach(cleanup => cleanup())
}, [isConnected, send, onMessage, provider, ...])
    // ↑ Having provider here causes infinite loops!
```

### After (Fixed):
```typescript
// Message handlers (runs once when connected)
useEffect(() => {
  // ... setup handlers, but only initialize if first load
  onMessage('model_settings_get', (data) => {
    if (data.success && !hasInitialized.current) {
      setProvider(data.llm_provider)
      hasInitialized.current = true
    }
  })
  
  return () => cleanups.forEach(cleanup => cleanup())
}, [isConnected, onMessage, send, testBeforeSave, provider, newApiKey, newBaseUrl])
  // ✅ providers and newApiKey removed from deps

// Initial load (runs once on mount)
useEffect(() => {
  if (!isConnected || hasInitialized.current) return
  
  send('model_providers_get')
  send('model_settings_get')
}, [isConnected, send])
  // ✅ Only depends on connection, not other state
```

## Additional Notes

- The backend API is working correctly
- The settings files (settings.json, .env) can be properly updated
- No database changes needed
- The fix is purely in the React component state management

## If Issues Persist

1. **Clear everything:**
   ```powershell
   # Delete .env file (except your API keys)
   # Or manually edit it to remove LLM_PROVIDER and VLM_PROVIDER variables
   ```

2. **Reset settings.json to default:**
   ```json
   {
     "proactive": {
       "enabled": true
     },
     "general": {
       "agent_name": "CraftBot"
     },
     "memory": {
       "enabled": true
     },
     "model": {
       "llm_provider": "anthropic",
       "vlm_provider": "anthropic"
     }
   }
   ```

3. **Restart everything:**
   - Close CraftBot
   - Clear browser cache
   - Run `python run.py` again

## Questions?
If you still have issues after these steps, check:
- Browser developer console (F12) for error messages
- That Node.js is installed and npm works: `npm --version`
- That you built the frontend: `npm run build`
- Browser is accessing the right URL
