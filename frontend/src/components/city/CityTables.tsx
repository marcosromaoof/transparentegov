"use client";

import { AgGridReact } from "ag-grid-react";

import type { CityProfile } from "@/lib/types";


export function CityTables({ profile }: { profile: CityProfile }) {
  return (
    <div className="grid-2">
      <div className="panel">
        <h3 className="section-title">Contratos Públicos</h3>
        <div className="table-wrap ag-theme-alpine" style={{ height: 300 }}>
          <AgGridReact
            rowData={profile.contracts}
            columnDefs={[
              { field: "id", headerName: "ID", maxWidth: 88 },
              { field: "supplier", headerName: "Fornecedor", flex: 1 },
              { field: "value", headerName: "Valor", maxWidth: 170 },
              { field: "start_date", headerName: "Início", maxWidth: 130 },
              { field: "end_date", headerName: "Fim", maxWidth: 130 }
            ]}
            defaultColDef={{ sortable: true, filter: true, resizable: true }}
          />
        </div>
      </div>

      <div className="panel">
        <h3 className="section-title">Gastos Públicos</h3>
        <div className="table-wrap ag-theme-alpine" style={{ height: 300 }}>
          <AgGridReact
            rowData={profile.spending}
            columnDefs={[
              { field: "year", headerName: "Ano", maxWidth: 98 },
              { field: "month", headerName: "Mês", maxWidth: 98 },
              { field: "category", headerName: "Categoria", flex: 1 },
              { field: "value", headerName: "Valor", maxWidth: 180 }
            ]}
            defaultColDef={{ sortable: true, filter: true, resizable: true }}
          />
        </div>
      </div>
    </div>
  );
}

