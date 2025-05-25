import { NextRequest, NextResponse } from 'next/server';
import { DPIStation, DPIResponse, DPIError } from '@/types/dpi';

export async function GET(request: NextRequest) {
  try {
    // GCP Cloud Function URL - you may need to update this with your actual function URL
    const GCP_FUNCTION_URL = process.env.GCP_API_FUNCTION_URL || 
      'https://us-central1-divvy-460820.cloudfunctions.net/divvy-api';
    
    console.log('Fetching DPI data from:', GCP_FUNCTION_URL);
    
    // Fetch data from the GCP Cloud Function
    const response = await fetch(GCP_FUNCTION_URL, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
      // Add cache control to ensure fresh data
      cache: 'no-store',
    });

    if (!response.ok) {
      console.error('GCP Function response not ok:', response.status, response.statusText);
      throw new Error(`Failed to fetch DPI data: ${response.status} ${response.statusText}`);
    }

    const dpiData: DPIStation[] = await response.json();
    
    console.log(`Successfully fetched ${dpiData.length} stations`);
    
    // Validate the data structure
    if (!Array.isArray(dpiData)) {
      throw new Error('Invalid data format: expected array of stations');
    }

    // Validate each station has required fields
    const validatedData = dpiData.filter(station => {
      return station.station_id && 
             station.station_name &&
             typeof station.overflow_per_dock === 'number' &&
             typeof station.pct_full === 'number' &&
             typeof station.dpi === 'number';
    });

    if (validatedData.length !== dpiData.length) {
      console.warn(`Filtered out ${dpiData.length - validatedData.length} invalid stations`);
    }

    // Sort by DPI in descending order (highest priority stations first)
    const sortedData = validatedData.sort((a, b) => b.dpi - a.dpi);

    // Add metadata for response
    const responseData: DPIResponse = {
      stations: sortedData,
      metadata: {
        total_stations: sortedData.length,
        last_updated: new Date().toISOString(),
        top_dpi: sortedData.length > 0 ? sortedData[0].dpi : 0,
        top_station_name: sortedData.length > 0 ? sortedData[0].station_name : 'N/A',
        data_source: 'GCP Cloud Function'
      }
    };

    return NextResponse.json(responseData, {
      status: 200,
      headers: {
        'Cache-Control': 'no-cache, no-store, must-revalidate',
        'Pragma': 'no-cache',
        'Expires': '0',
      },
    });

  } catch (error) {
    console.error('Error fetching DPI data:', error);
    
    const errorResponse: DPIError = {
      error: 'Failed to fetch DPI data',
      message: error instanceof Error ? error.message : 'Unknown error',
      stations: [],
      metadata: {
        total_stations: 0,
        last_updated: new Date().toISOString(),
        top_dpi: 0,
        top_station_name: 'N/A',
        data_source: 'Error'
      }
    };

    return NextResponse.json(errorResponse, { status: 500 });
  }
}

// Optional: Add a POST method for testing
export async function POST(request: NextRequest) {
  return NextResponse.json(
    { message: 'POST method not supported for DPI endpoint' },
    { status: 405 }
  );
} 