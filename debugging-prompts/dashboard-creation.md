# Dashboard Creation Implementation Guide

## 🎯 Project Status
✅ **API Route Complete**: `/api/dpi` is working and returning 950 stations  
✅ **Data Pipeline**: GCP functions are processing live data every 20 minutes  
✅ **Next Step**: Create dashboard UI to display DPI rankings with scatter plot analysis  

---

## 📊 Current Data Structure

### API Endpoint
- **URL**: `http://localhost:3000/api/dpi`
- **Method**: GET
- **Response Format**: JSON
- **Cache Strategy**: 24-hour cache (data updates daily at 2:15 AM)

### Data Schema
```typescript
interface DPIResponse {
  stations: DPIStation[];
  metadata: {
    total_stations: number;
    last_updated: string;
    top_dpi: number;
    data_source: string;
  };
}

interface DPIStation {
  station_id: string;           // e.g., "13053", "TA1309000030"
  overflow_per_dock: number;    // Net overflow divided by capacity
  pct_full: number;            // Percentage of time station is full (0-1)
  dpi: number;                 // DPI metric (overflow_per_dock * pct_full)
}
```

### Sample Response
```json
{
  "stations": [
    {
      "station_id": "13053",
      "overflow_per_dock": 48.364,
      "pct_full": 1.0,
      "dpi": 48.364
    },
    {
      "station_id": "TA1309000030", 
      "overflow_per_dock": 44.267,
      "pct_full": 1.0,
      "dpi": 44.267
    },
    {
      "station_id": "chargingstx07",
      "overflow_per_dock": 48.625,
      "pct_full": 0.5,
      "dpi": 24.313
    }
  ],
  "metadata": {
    "total_stations": 950,
    "last_updated": "2025-05-25T01:26:23.402Z",
    "top_dpi": 48.364,
    "data_source": "GCP Cloud Function"
  }
}
```

---

## 🎨 Enhanced Dashboard Design Requirements

### Page Layout: `/app/(report)/page.tsx`
```
┌─────────────────────────────────────────────────────────────┐
│                    Divvy Live Dashboard                     │
│                                                             │
│  📊 Summary Cards                                           │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐          │
│  │Total Stations│ │  Top DPI    │ │Last Updated │          │
│  │     950      │ │   48.364    │ │  2 min ago  │          │
│  └─────────────┘ └─────────────┘ └─────────────┘          │
│                                                             │
│  🚲 Station Rankings (Top 20)                              │
│  ┌─────────────────────────────────────────────────────────┐│
│  │Rank│Station ID    │Overflow/Dock│% Full│DPI   │Priority ││
│  ├────┼──────────────┼─────────────┼──────┼──────┼─────────┤│
│  │ 1  │13053         │    48.36    │100%  │48.364│🔴 HIGH  ││
│  │ 2  │TA1309000030 │    44.27    │100%  │44.267│🔴 HIGH  ││
│  │ 3  │chargingstx07 │    48.63    │ 50%  │24.313│🟡 MED   ││
│  └─────────────────────────────────────────────────────────┘│
│                                                             │
│  📈 Station Analysis Scatter Plot                          │
│  ┌─────────────────────────────────────────────────────────┐│
│  │                    % Time Full (100%)                   ││
│  │                         ▲                               ││
│  │   🚲 Needs Racks    │    │    🚐 Needs Vans            ││
│  │   (High DPI)        │    │    (Rebalancing)            ││
│  │   • • •             │    │             • •             ││
│  │                     │    │                             ││
│  │ ────────────────────┼────┼──────────────────────────► ││
│  │                     │    │                Overflow/Dock││
│  │   📊 Needs Usage    │    │    ✅ Optimal               ││
│  │   Boost             │    │    (Fine as-is)             ││
│  │   •                 │    │                •            ││
│  │                    (0%)  │                             ││
│  └─────────────────────────────────────────────────────────┘│
│                                                             │
│  📈 Show All Stations (950 total) [Button]                 │
└─────────────────────────────────────────────────────────────┘
```

### Scatter Plot Quadrant Analysis
| Quadrant | X-Axis (Overflow/Dock) | Y-Axis (% Time Full) | Interpretation | Action Needed |
|----------|------------------------|---------------------|----------------|---------------|
| **🚲 Top-Right** | High | High | **Needs More Racks** - Station attracts bikes AND frequently full | Add docks + increase rebalancing |
| **🚐 Top-Left** | Low | High | **Needs More Vans** - Fills quickly but drains quickly | More frequent rebalancing |
| **📊 Bottom-Right** | High | Low | **Needs Usage Boost** - Bikes accumulate but rarely full | Marketing/pricing to increase usage |
| **✅ Bottom-Left** | Low | Low | **Optimal** - Balanced usage and capacity | No action needed |

### Priority Color Coding
- 🔴 **HIGH** (DPI > 20): Red badge - Urgent need for more racks
- 🟡 **MEDIUM** (DPI 5-20): Yellow badge - Moderate need
- 🟢 **LOW** (DPI < 5): Green badge - Adequate capacity

---

## 🛠 Implementation Steps

### Step 1: Create Dashboard Page Structure
**File**: `website-reporting/src/app/(report)/page.tsx`
- [ ] Create main dashboard layout
- [ ] Add summary cards component
- [ ] Add station rankings table
- [ ] Add scatter plot visualization component
- [ ] Implement data fetching with 24-hour cache
- [ ] Add loading and error states

### Step 2: Build Summary Cards Component
**File**: `website-reporting/src/components/SummaryCards.tsx`
- [ ] Total stations card
- [ ] Top DPI value card  
- [ ] Last updated timestamp card
- [ ] Use shadcn `Card` component

### Step 3: Build Station Rankings Table
**File**: `website-reporting/src/components/StationRankingsTable.tsx`
- [ ] Use shadcn `Table` component
- [ ] Add rank column (1, 2, 3...)
- [ ] Format numbers (2 decimal places)
- [ ] Add priority badges using shadcn `Badge`
- [ ] Implement pagination/show more functionality

### Step 4: Build Scatter Plot Component
**File**: `website-reporting/src/components/DPIScatterPlot.tsx`
- [ ] Use `recharts` ScatterChart component
- [ ] X-axis: Overflow per dock
- [ ] Y-axis: % time full (0-100%)
- [ ] Color code points by DPI priority level
- [ ] Add quadrant labels and background shading
- [ ] Add hover tooltips with station details
- [ ] Add quadrant interpretation legend

### Step 5: Add Priority Badge Component
**File**: `website-reporting/src/components/PriorityBadge.tsx`
- [ ] Calculate priority level from DPI value
- [ ] Return colored badge with appropriate text
- [ ] Use shadcn `Badge` with variants

### Step 6: Add Data Fetching Hook with Caching
**File**: `website-reporting/src/hooks/useDPIData.ts`
- [ ] Create custom hook for fetching DPI data
- [ ] Implement 24-hour cache using SWR or React Query
- [ ] Handle loading, error, and success states
- [ ] Type the response properly
- [ ] Add cache invalidation strategy

### Step 7: Style and Polish
- [ ] Add responsive design for mobile
- [ ] Add hover effects on table rows and scatter plot points
- [ ] Add sorting capabilities (by DPI, station ID, etc.)
- [ ] Add search/filter functionality
- [ ] Ensure scatter plot is responsive

---

## 🎯 Key Features to Implement

### Core Features (MVP)
1. **Live Data Display**: Show current DPI rankings with 24-hour cache
2. **Priority Visualization**: Color-coded priority levels
3. **Summary Metrics**: Key stats at the top
4. **Responsive Table**: Top 20 stations with expand option
5. **Scatter Plot Analysis**: 2x2 quadrant visualization for strategic insights

### Enhanced Features (Future)
1. **Real-time Updates**: Auto-refresh when cache expires
2. **Historical Trends**: Show DPI changes over time
3. **Station Details**: Click to see individual station info
4. **Map Integration**: Show stations on Chicago map
5. **Alerts**: Notify when stations reach critical DPI levels
6. **Interactive Scatter Plot**: Click points to highlight in table

---

## 📦 Required Dependencies

### Already Available
- ✅ `@radix-ui/react-slot` - For shadcn components
- ✅ `lucide-react` - For icons
- ✅ `tailwind-merge` - For styling
- ✅ `class-variance-authority` - For component variants

### Need to Add
- [ ] `swr` or `@tanstack/react-query` - For data fetching with caching
- [ ] `recharts` - For scatter plot visualization
- [ ] `date-fns` - For date formatting

### Installation Commands
```bash
cd website-reporting
npm install swr recharts date-fns
# OR for React Query
npm install @tanstack/react-query recharts date-fns
```

---

## 🚀 Getting Started

1. **Start Development Server**:
   ```bash
   cd website-reporting
   npm run dev
   ```

2. **Test API Endpoint**:
   ```bash
   curl http://localhost:3000/api/dpi | jq '.metadata'
   ```

3. **Begin Implementation**:
   - Start with Step 1: Create the main dashboard page
   - Use existing shadcn components: `Card`, `Table`, `Badge`
   - Add recharts for scatter plot visualization
   - Follow the enhanced design mockup above

---

## 🔄 Caching Strategy

### Data Fetching with 24-Hour Cache
```typescript
// Using SWR
const { data, error, isLoading } = useSWR(
  '/api/dpi',
  fetcher,
  {
    refreshInterval: 0, // Disable auto-refresh
    revalidateOnFocus: false,
    revalidateOnReconnect: false,
    dedupingInterval: 24 * 60 * 60 * 1000, // 24 hours
  }
);

// Using React Query
const { data, error, isLoading } = useQuery({
  queryKey: ['dpi-data'],
  queryFn: fetchDPIData,
  staleTime: 24 * 60 * 60 * 1000, // 24 hours
  cacheTime: 24 * 60 * 60 * 1000, // 24 hours
});
```

### Cache Invalidation
- **Automatic**: Cache expires after 24 hours
- **Manual**: Provide refresh button for immediate updates
- **Smart**: Check `last_updated` timestamp to determine if new data is available

---

## 📊 Scatter Plot Implementation Details

### Chart Configuration
```typescript
interface ScatterPlotProps {
  data: DPIStation[];
}

const DPIScatterPlot = ({ data }: ScatterPlotProps) => {
  const chartData = data.map(station => ({
    x: station.overflow_per_dock,
    y: station.pct_full * 100, // Convert to percentage
    dpi: station.dpi,
    station_id: station.station_id,
    priority: getPriorityLevel(station.dpi),
  }));

  return (
    <ResponsiveContainer width="100%" height={400}>
      <ScatterChart data={chartData}>
        <XAxis 
          dataKey="x" 
          name="Overflow per Dock"
          label={{ value: 'Overflow per Dock', position: 'insideBottom', offset: -10 }}
        />
        <YAxis 
          dataKey="y" 
          name="% Time Full"
          label={{ value: '% Time Full', angle: -90, position: 'insideLeft' }}
        />
        <Scatter 
          dataKey="y" 
          fill={(entry) => getPriorityColor(entry.priority)}
        />
        <Tooltip content={<CustomTooltip />} />
      </ScatterChart>
    </ResponsiveContainer>
  );
};
```

### Quadrant Visualization
- **Background shading**: Light colors to indicate quadrant meanings
- **Axis lines**: Clear division at median values
- **Labels**: Text overlays explaining each quadrant
- **Legend**: Color coding explanation

---

## 📝 Notes

- **Data Updates**: The rollup function runs daily at 2:15 AM, scraper runs every 20 minutes
- **Station IDs**: Mix of numeric (legacy) and alphanumeric (new) formats
- **DPI Calculation**: `overflow_per_dock * pct_full` - higher values = more urgent need
- **Performance**: 950 stations is manageable for scatter plot, but consider data sampling for very large datasets
- **Caching**: 24-hour cache aligns with daily data updates, reducing API calls and improving performance

---

## 🎨 Design System

### Colors (Tailwind)
- **High Priority**: `bg-red-100 text-red-800` (red badge/points)
- **Medium Priority**: `bg-yellow-100 text-yellow-800` (yellow badge/points)  
- **Low Priority**: `bg-green-100 text-green-800` (green badge/points)
- **Background**: `bg-gray-50` for page background
- **Cards**: `bg-white` with `shadow-sm`
- **Scatter Plot**: 
  - High DPI: `#ef4444` (red-500)
  - Medium DPI: `#f59e0b` (amber-500)
  - Low DPI: `#10b981` (emerald-500)

### Typography
- **Page Title**: `text-3xl font-bold`
- **Card Titles**: `text-lg font-semibold`
- **Table Headers**: `text-sm font-medium text-gray-500`
- **Numbers**: `font-mono` for consistent alignment
- **Scatter Plot Labels**: `text-sm font-medium`

### Scatter Plot Quadrant Colors
- **Top-Right (Needs Racks)**: Light red background `bg-red-50`
- **Top-Left (Needs Vans)**: Light blue background `bg-blue-50`
- **Bottom-Right (Needs Usage)**: Light yellow background `bg-yellow-50`
- **Bottom-Left (Optimal)**: Light green background `bg-green-50`
