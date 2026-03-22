Ejecutá un análisis completo del proyecto con Kagami MCP. Corré TODOS los tools en este orden y mostrá los resultados:

1. `index_project` — indexar el repo
2. `bug_prediction` — heatmap de riesgo (qué archivos van a dar problemas)
3. `detect_drift` — docs desactualizados vs código
4. `neighborhoods` — mapa de comunidades del código
5. `analyze_health` — code smells y complejidad
6. `time_machine` para los 3 archivos con más riesgo del bug_prediction

Al final, hacé un resumen ejecutivo con:
- Estado general del proyecto (sano/atención/crítico)
- Top 3 archivos más riesgosos y por qué
- Docs que necesitan actualización
- Comunidades que necesitan atención
- Acción inmediata recomendada
