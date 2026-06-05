-- Training database schema for SQL lessons.
-- Domain: office chair furniture production.
-- Target database: PostgreSQL 16+.
-- This script only defines training tables; it does not insert sample data.

CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE chair_models (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    model_code text NOT NULL,
    model_name text NOT NULL,
    category text NOT NULL,
    status text NOT NULL DEFAULT 'active',
    standard_labor_minutes integer NOT NULL DEFAULT 0,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),

    CONSTRAINT chair_models_model_code_unique UNIQUE (model_code),
    CONSTRAINT chair_models_status_check
        CHECK (status IN ('active', 'archived', 'test')),
    CONSTRAINT chair_models_standard_labor_minutes_check
        CHECK (standard_labor_minutes >= 0)
);

CREATE TABLE suppliers (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    supplier_code text NOT NULL,
    supplier_name text NOT NULL,
    contact_name text,
    phone text,
    email text,
    city text,
    status text NOT NULL DEFAULT 'active',
    created_at timestamptz NOT NULL DEFAULT now(),

    CONSTRAINT suppliers_supplier_code_unique UNIQUE (supplier_code),
    CONSTRAINT suppliers_status_check
        CHECK (status IN ('active', 'reserve', 'blocked'))
);

CREATE TABLE materials (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    material_code text NOT NULL,
    material_name text NOT NULL,
    category text NOT NULL,
    unit text NOT NULL,
    default_supplier_id uuid REFERENCES suppliers(id) ON DELETE SET NULL,
    current_price numeric(12, 2),
    min_stock_quantity numeric(14, 3) NOT NULL DEFAULT 0,
    status text NOT NULL DEFAULT 'active',
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),

    CONSTRAINT materials_material_code_unique UNIQUE (material_code),
    CONSTRAINT materials_current_price_check
        CHECK (current_price IS NULL OR current_price >= 0),
    CONSTRAINT materials_min_stock_quantity_check
        CHECK (min_stock_quantity >= 0),
    CONSTRAINT materials_status_check
        CHECK (status IN ('active', 'archived', 'replacement'))
);

CREATE TABLE bom_headers (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    chair_model_id uuid NOT NULL REFERENCES chair_models(id) ON DELETE CASCADE,
    bom_code text NOT NULL,
    version text NOT NULL,
    status text NOT NULL DEFAULT 'draft',
    valid_from date NOT NULL,
    valid_to date,
    comment text,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),

    CONSTRAINT bom_headers_bom_code_version_unique UNIQUE (bom_code, version),
    CONSTRAINT bom_headers_status_check
        CHECK (status IN ('draft', 'active', 'archived')),
    CONSTRAINT bom_headers_valid_dates_check
        CHECK (valid_to IS NULL OR valid_to >= valid_from)
);

CREATE TABLE bom_lines (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    bom_header_id uuid NOT NULL REFERENCES bom_headers(id) ON DELETE CASCADE,
    material_id uuid NOT NULL REFERENCES materials(id) ON DELETE RESTRICT,
    quantity_per_unit numeric(14, 4) NOT NULL,
    scrap_percent numeric(6, 3) NOT NULL DEFAULT 0,
    line_type text NOT NULL DEFAULT 'main_material',
    comment text,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),

    CONSTRAINT bom_lines_bom_material_unique
        UNIQUE (bom_header_id, material_id),
    CONSTRAINT bom_lines_quantity_per_unit_check
        CHECK (quantity_per_unit > 0),
    CONSTRAINT bom_lines_scrap_percent_check
        CHECK (scrap_percent >= 0),
    CONSTRAINT bom_lines_line_type_check
        CHECK (line_type IN (
            'main_material',
            'component',
            'packaging',
            'consumable'
        ))
);

CREATE TABLE warehouse_stocks (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    material_id uuid NOT NULL REFERENCES materials(id) ON DELETE CASCADE,
    warehouse_name text NOT NULL,
    quantity_on_hand numeric(14, 3) NOT NULL DEFAULT 0,
    reserved_quantity numeric(14, 3) NOT NULL DEFAULT 0,
    available_quantity numeric(14, 3) NOT NULL DEFAULT 0,
    last_counted_at timestamptz,
    updated_at timestamptz NOT NULL DEFAULT now(),

    CONSTRAINT warehouse_stocks_material_warehouse_unique
        UNIQUE (material_id, warehouse_name),
    CONSTRAINT warehouse_stocks_reserved_quantity_check
        CHECK (reserved_quantity >= 0),
    CONSTRAINT warehouse_stocks_available_quantity_check
        CHECK (available_quantity = quantity_on_hand - reserved_quantity)
);

CREATE TABLE production_plan (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    plan_date date NOT NULL,
    chair_model_id uuid NOT NULL REFERENCES chair_models(id) ON DELETE RESTRICT,
    planned_quantity integer NOT NULL,
    shift_name text,
    plan_version text NOT NULL DEFAULT 'base',
    status text NOT NULL DEFAULT 'draft',
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),

    CONSTRAINT production_plan_planned_quantity_check
        CHECK (planned_quantity >= 0),
    CONSTRAINT production_plan_status_check
        CHECK (status IN ('draft', 'approved', 'cancelled', 'completed'))
);

CREATE TABLE production_output (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    output_date date NOT NULL,
    chair_model_id uuid NOT NULL REFERENCES chair_models(id) ON DELETE RESTRICT,
    production_plan_id uuid REFERENCES production_plan(id) ON DELETE SET NULL,
    produced_quantity integer NOT NULL,
    defect_quantity integer NOT NULL DEFAULT 0,
    shift_name text,
    comment text,
    created_at timestamptz NOT NULL DEFAULT now(),

    CONSTRAINT production_output_produced_quantity_check
        CHECK (produced_quantity >= 0),
    CONSTRAINT production_output_defect_quantity_check
        CHECK (defect_quantity >= 0),
    CONSTRAINT production_output_defect_lte_produced_check
        CHECK (defect_quantity <= produced_quantity)
);

CREATE TABLE warehouse_movements (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    material_id uuid NOT NULL REFERENCES materials(id) ON DELETE RESTRICT,
    movement_date date NOT NULL,
    movement_type text NOT NULL,
    quantity numeric(14, 3) NOT NULL,
    warehouse_name text NOT NULL,
    document_number text,
    reason text,
    production_output_id uuid REFERENCES production_output(id) ON DELETE SET NULL,
    created_at timestamptz NOT NULL DEFAULT now(),

    CONSTRAINT warehouse_movements_quantity_check
        CHECK (quantity <> 0),
    CONSTRAINT warehouse_movements_type_check
        CHECK (movement_type IN (
            'receipt',
            'write_off',
            'transfer',
            'adjustment',
            'return'
        ))
);

CREATE INDEX chair_models_status_idx
    ON chair_models (status);

CREATE INDEX suppliers_status_idx
    ON suppliers (status);

CREATE INDEX materials_category_idx
    ON materials (category);

CREATE INDEX materials_default_supplier_id_idx
    ON materials (default_supplier_id);

CREATE INDEX materials_status_idx
    ON materials (status);

CREATE INDEX bom_headers_chair_model_id_idx
    ON bom_headers (chair_model_id);

CREATE INDEX bom_headers_status_idx
    ON bom_headers (status);

CREATE INDEX bom_lines_bom_header_id_idx
    ON bom_lines (bom_header_id);

CREATE INDEX bom_lines_material_id_idx
    ON bom_lines (material_id);

CREATE INDEX warehouse_stocks_material_id_idx
    ON warehouse_stocks (material_id);

CREATE INDEX warehouse_stocks_warehouse_name_idx
    ON warehouse_stocks (warehouse_name);

CREATE INDEX warehouse_movements_material_date_idx
    ON warehouse_movements (material_id, movement_date DESC);

CREATE INDEX warehouse_movements_type_idx
    ON warehouse_movements (movement_type);

CREATE INDEX warehouse_movements_production_output_id_idx
    ON warehouse_movements (production_output_id);

CREATE INDEX production_plan_date_idx
    ON production_plan (plan_date);

CREATE INDEX production_plan_chair_model_date_idx
    ON production_plan (chair_model_id, plan_date);

CREATE INDEX production_plan_status_idx
    ON production_plan (status);

CREATE INDEX production_output_date_idx
    ON production_output (output_date);

CREATE INDEX production_output_chair_model_date_idx
    ON production_output (chair_model_id, output_date);

CREATE INDEX production_output_plan_id_idx
    ON production_output (production_plan_id);
