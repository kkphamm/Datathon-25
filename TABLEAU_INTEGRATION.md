# 📊 Tableau Dashboard Integration Guide

## How the Dynamic Dashboard Works

The Tableau dashboard automatically updates when you submit your college preferences! Here's how it works:

### ✨ Features

1. **Automatic Filtering** - When you click "Get Recommendations", the dashboard filters update to match your preferences
2. **Synchronized View** - See both your ranked recommendations AND the filtered data visualized in Tableau
3. **Reset Filters** - Click the "Reset Filters" button to see all colleges again
4. **Auto-Scroll** - After getting recommendations, the page smoothly scrolls to the dashboard

---

## 🔧 What Gets Filtered

When you submit your preferences, the following filters are applied to the Tableau dashboard:

### 1. **State Filter**
- If you select a preferred state, only colleges in that state will show
- Leave empty to see all states

### 2. **Net Price Range**
- Filters colleges to only show those under your maximum net price
- Range: $0 to your selected max price

### 3. **Graduation Rate**
- Shows only colleges above your minimum graduation rate threshold
- Range: Your minimum to 100%

### 4. **Retention Rate**
- Filters by your minimum retention rate requirement
- Range: Your minimum to 100%

### 5. **MSI Status**
- If you select MSI preferences (HSI, HBCU, etc.), only those types will show
- Multiple selections work together

---

## 📋 Required Tableau Setup

For the filters to work, your Tableau dashboard must have these fields available:

### Required Fields in Tableau:
1. `State Abbreviation` (dimension)
2. `Net Price` (measure)
3. `Bachelor's Degree Graduation Rate Bachelor Degree Within 6 Years - Total` (measure)
4. `First-Time, Full-Time Retention Rate` (measure)
5. `HSI`, `PBI`, `HBCU`, `AANAPII`, `ANNHI`, `TRIBAL`, `NANTI` (dimensions)

### Tableau Dashboard Tips:
- **Use the `all_colleges_scored.csv`** file as your data source
- **Add these fields to your visualizations** so filters can be applied
- **Test filters manually** in Tableau first to ensure they work
- **Publish to Tableau Public** to get the shareable URL

---

## 🔍 How to Debug

### Check if Tableau is loaded:
Open browser console (F12) and look for:
```
Tableau dashboard loaded successfully!
```

### Check if filters are applied:
After clicking "Get Recommendations", look for:
```
Tableau filters applied successfully!
```

### Common Issues:

**❌ "Tableau viz not initialized yet"**
- Wait a few seconds for Tableau to fully load
- Refresh the page and try again

**❌ Filters not working**
- Check that field names in Tableau match exactly
- Ensure fields are included in the dashboard worksheets
- Try the "Reset Filters" button first

**❌ Dashboard not scrolling**
- Make sure you clicked "Get Recommendations"
- Check browser console for JavaScript errors

---

## 🎯 Customizing Filters

### To modify which filters are applied:

Edit `script.js` in the `updateTableauFilters()` function around line 136.

**Example: Add a new filter**
```javascript
// Filter by region
if (preferences.region) {
    worksheet.applyFilterAsync('Region', preferences.region, tableau.FilterUpdateType.REPLACE);
}
```

**Example: Change filter ranges**
```javascript
// Only show colleges under $20k (hardcoded)
worksheet.applyRangeFilterAsync('Net Price', {
    min: 0,
    max: 20000
}, tableau.FilterUpdateType.REPLACE);
```

---

## 🔄 Workflow

1. **User adjusts sliders** → Sets preferences
2. **User clicks "Get Recommendations"** → API call to Flask
3. **Results displayed** → Top N colleges shown in cards
4. **Filters applied to Tableau** → Dashboard updates automatically
5. **Page scrolls** → User sees filtered dashboard
6. **User can click "Reset Filters"** → Dashboard shows all colleges again

---

## 📚 Tableau JavaScript API Reference

The integration uses Tableau's JavaScript API v2:

**Key Functions Used:**
- `tableau.Viz()` - Creates the visualization
- `workbook.getWorkbook()` - Gets workbook object
- `workbook.getActiveSheet()` - Gets current sheet
- `worksheet.applyFilterAsync()` - Applies categorical filter
- `worksheet.applyRangeFilterAsync()` - Applies range filter
- `worksheet.clearFilterAsync()` - Removes filter

**Official Documentation:**
https://help.tableau.com/current/api/js_api/en-us/JavaScriptAPI/js_api.htm

---

## 🎨 Customizing the Dashboard URL

To use a different Tableau dashboard:

1. **Update the URL** in `script.js` line 136:
```javascript
const url = 'https://public.tableau.com/views/YourWorkbook/YourDashboard';
```

2. **Update filter field names** in the `updateTableauFilters()` function to match your dashboard's fields

3. **Test thoroughly** to ensure all filters work

---

## ✅ Testing Checklist

- [ ] Dashboard loads when page opens
- [ ] Console shows "Tableau dashboard loaded successfully!"
- [ ] Clicking "Get Recommendations" shows results
- [ ] Dashboard filters update automatically
- [ ] Page scrolls to dashboard section
- [ ] Console shows "Tableau filters applied successfully!"
- [ ] "Reset Filters" button clears all filters
- [ ] Dashboard shows all colleges after reset
- [ ] Works on mobile devices
- [ ] Works in different browsers (Chrome, Firefox, Edge, Safari)

---

## 🚀 Advanced Features

### Add a Loading Indicator for Tableau
```javascript
function initTableau() {
    // Show loading
    const loading = document.createElement('div');
    loading.textContent = 'Loading Tableau dashboard...';
    loading.style.textAlign = 'center';
    loading.style.padding = '2rem';
    containerDiv.appendChild(loading);
    
    const options = {
        onFirstInteractive: function() {
            loading.remove(); // Remove loading message
            console.log('Tableau dashboard loaded!');
        }
    };
    
    tableauViz = new tableau.Viz(containerDiv, url, options);
}
```

### Highlight Selected Colleges
```javascript
// After applying filters, highlight the top recommendation
function highlightTopCollege(collegeName) {
    const workbook = tableauViz.getWorkbook();
    const activeSheet = workbook.getActiveSheet();
    const worksheets = activeSheet.getWorksheets();
    
    worksheets.forEach(worksheet => {
        worksheet.selectMarksAsync('Institution Name', collegeName, 
            tableau.SelectionUpdateType.REPLACE);
    });
}
```

---

**Questions? Check the browser console (F12) for detailed error messages and logs!**

