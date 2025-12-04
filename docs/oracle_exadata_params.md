# Oracle 19c Exadata Parameter Hints for Large Fact/Dimension Workloads

The table below lists common initialization parameters to review on Exadata when optimizing large fact tables and dimensions, together with the dynamic views where you can check current or SPFILE values.

| Bereich | Parameter | Hinweise | Typische Sicht |
| --- | --- | --- | --- |
| Speicher (PGA/SGA) | `memory_target`, `memory_max_target` (oder `sga_target` + `pga_aggregate_target`) | Ausreichend Speicher für Hash-Joins und Sorts bereitstellen; bei AMM entweder beide Memory-Targets setzen oder klassisch SGA/PGA. | `V$PARAMETER` / `V$SYSTEM_PARAMETER` für laufende Werte, `V$SPPARAMETER` für SPFILE |
| Speicher (PGA) | `pga_aggregate_limit`, `_pga_max_size` | `pga_aggregate_limit` begrenzt die PGA gesamt; `_pga_max_size` nur vorsichtig anheben und testen. | `V$PARAMETER` / `V$SYSTEM_PARAMETER` |
| Result Cache | `result_cache_max_size` | Bei DWH oft klein oder 0; nur nutzen, wenn viele wiederholte Ergebnisse. | `V$PARAMETER` |
| Parallelisierung | `parallel_degree_policy`, `parallel_degree_limit`, `parallel_min_servers`, `parallel_max_servers`, `parallel_servers_target`, `parallel_min_time_threshold` | Auto DOP steuert Grad der Parallelisierung; harte und weiche Limits setzen, damit Lastspitzen kontrollierbar bleiben. | `V$SYSTEM_PARAMETER` (instanzweit), `GV$PARAMETER` für RAC-Gesamtüberblick |
| In-Memory | `inmemory_force`, `inmemory_size` | Selektiv für große Fakten-Tabellen; Dimensionen oft In-Memory columnar. | `V$INMEMORY_AREA`, `V$PARAMETER` |
| Optimizer | `optimizer_adaptive_plans`, `optimizer_adaptive_statistics`, `optimizer_features_enable`, `optimizer_dynamic_sampling`, `_optimizer_use_feedback`, `_optimizer_gather_feedback` | Adaptive Features je nach Kardinalitätsschwankung prüfen; 19c-Standard beibehalten. | `V$SYSTEM_PARAMETER`, Historie über `DBA_HIST_PARAMETER` |
| Cursor-Sharing | `cursor_sharing` | Nur bei vielen Literal-Varianten auf `FORCE`, sonst `EXACT`. | `V$PARAMETER` |
| Logging/Undo | `undo_tablespace`, `undo_retention` | Genügend Undo für lange parallele Abfragen vorhalten. | `V$PARAMETER`, Tablespace-Größe über `DBA_DATA_FILES` |
| I/O & Exadata | `db_file_multiblock_read_count`, `filesystemio_options`, `cell_offload_processing`, `_serial_direct_read` | Exadata Smart Scan nicht behindern; Direct Path Reads bei großen Scans erlauben. | `V$SYSTEM_PARAMETER`, Cell-Offload-Status zusätzlich in `V$CELL_STATE` |
| Sicherheit | `db_block_checksum`, `db_lost_write_protect` | Standard meist beibehalten; Performance vs. Sicherheit abwägen. | `V$SYSTEM_PARAMETER` |
| Ressourcensteuerung | `cpu_count`, `_resource_manager_cpu_allocation`, Resource Manager-PDB-Einstellungen (`parallel_server_limit`) | Instance Caging und Consumer Groups verhindern Blockaden zwischen ETL/Reporting. | `V$SYSTEM_PARAMETER`, Resource Manager in `DBA_RSRC_CONSUMER_GROUPS` |
| Parallel DDL | `parallel_ddl_enable_default` | Für schnelle Index-/Partition-Rebuilds per Parallel DDL aktivieren. | `V$PARAMETER` |

## Wichtige Sichten im Detail

- **`V$PARAMETER` / `V$SYSTEM_PARAMETER`**: Aktuelle Parameterwerte; `ISDEFAULT`, `ISSPECIFIED` und `ISMODIFIED` zeigen die Quelle. `GV$PARAMETER` für RAC-weit.
- **`V$SPPARAMETER`**: Werte im SPFILE. Nützlich, um geplante Änderungen vs. laufende Instanz zu vergleichen.
- **`DBA_HIST_PARAMETER`**: AWR-Historie von Parametern, um Änderungen über die Zeit nachzuvollziehen.
- **`V$INMEMORY_AREA`**: Übersicht über die In-Memory-Größe und Nutzung.
- **`V$CELL_STATE`**: Statusinformationen zu Exadata Storage Cells, u. a. Offload-Fähigkeit.

Für Abfragen nutzen Sie je nach Bedarf Filter auf `NAME`, `ISDEFAULT` und `ISMODIFIED`, z. B.:

```sql
SELECT name, value, issys_modifiable, isdefault, ismodified
FROM   v$system_parameter
WHERE  name IN (
         'parallel_degree_policy',
         'parallel_degree_limit',
         'parallel_min_servers',
         'parallel_max_servers',
         'parallel_servers_target',
         'parallel_min_time_threshold'
       );
``` 
