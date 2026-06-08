from django.db import migrations


CREATE_TRIGGER = """
CREATE OR REPLACE FUNCTION prevent_negative_product_quantity()
RETURNS trigger AS $$
BEGIN
    IF NEW.quantity < 0 THEN
        RAISE EXCEPTION 'Product quantity cannot be negative';
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS product_quantity_non_negative ON warehouse_product;
CREATE TRIGGER product_quantity_non_negative
BEFORE INSERT OR UPDATE OF quantity ON warehouse_product
FOR EACH ROW
EXECUTE FUNCTION prevent_negative_product_quantity();
"""

DROP_TRIGGER = """
DROP TRIGGER IF EXISTS product_quantity_non_negative ON warehouse_product;
DROP FUNCTION IF EXISTS prevent_negative_product_quantity();
"""


class Migration(migrations.Migration):
    dependencies = [
        ("warehouse", "0003_warehouse_performance_indexes"),
    ]

    operations = [
        migrations.RunSQL(sql=CREATE_TRIGGER, reverse_sql=DROP_TRIGGER),
    ]
