// Types for the DPI data structure
export interface DPIStation {
  station_id: string;
  station_name: string;
  overflow_per_dock: number;
  pct_full: number;
  dpi: number;
}

export interface StationWithMetadata extends DPIStation {
  name?: string;
  lat?: number;
  lon?: number;
  capacity?: number;
}

export interface DPIResponse {
  stations: DPIStation[];
  metadata: {
    total_stations: number;
    last_updated: string;
    top_dpi: number;
    top_station_name: string;
    data_source: string;
  };
}

export interface DPIError {
  error: string;
  message: string;
  stations: never[];
  metadata: {
    total_stations: 0;
    last_updated: string;
    top_dpi: 0;
    top_station_name: 'N/A';
    data_source: 'Error';
  };
} 