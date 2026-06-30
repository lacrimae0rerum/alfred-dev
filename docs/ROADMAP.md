# Alfred Codex Roadmap

## Estado Actual

Alfred Codex ya existe como MVP funcional en un repositorio standalone.
No es paridad completa con Alfred Dev: es una primera versión nativa para Codex
que conserva los flujos, la memoria básica y las garantías mínimas de validación
sin depender de superficies Claude-only.

## Hecho

- Plugin Codex válido con `.codex-plugin/plugin.json`.
- Skill principal `alfred-for-codex` como entrada única.
- Flujos MVP: `feature`, `quick`, `fix`, `spike`, `audit`, `ship`.
- Runtime Python `alfred_core/` con:
  - definición de flujos y fases;
  - gates de calidad;
  - autopilot básico;
  - catálogo de agentes opcionales;
  - rutas neutrales bajo `.codex/alfred/`;
  - configuración local;
  - memoria SQLite;
  - sanitización de secretos.
- MCP `alfred-memory` con herramientas seguras para:
  - iniciar iteraciones;
  - registrar decisiones;
  - registrar eventos;
  - buscar memoria;
  - consultar iteraciones;
  - consultar estadísticas.
- Documentación base:
  - PRD;
  - roadmap;
  - bugs/gaps;
  - README mínimo.
- Tests de validación:
  - manifest;
  - skill;
  - flujos;
  - gates;
  - rutas;
  - memoria;
  - MCP;
  - sanitización;
  - seguridad de documentación pública.
- Review y correcciones posteriores:
  - una gate de usuario ya no puede avanzar un resultado rechazado;
  - el MCP ya no escribe memoria dentro del repo del plugin sin contexto de proyecto.
- Instalación local verificada:
  - marketplace standalone `alfred-codex-local` registrado;
  - plugin `alfred-codex@alfred-codex-local` instalado y habilitado;
  - Codex Desktop abierto con el workspace del repo.

## Validación Actual

- `python3 -m unittest discover -s tests -v`: 24 tests pasan.
- Codex plugin validator: pasa.
- Skill validator: pasa.
- Smoke MCP:
  - sin contexto de proyecto falla de forma limpia;
  - con `project_dir` explícito funciona y escribe en `.codex/alfred/memory.db`.
- Instalación Codex:
  - `codex plugin list` muestra `alfred-codex@alfred-codex-local` como `installed, enabled`.
  - `codex app .` abre Codex Desktop con el workspace.

## Pendiente Inmediato

1. Añadir helpers operativos.
   - `start`, `status`, `resume`, `pause`, `verify`.
   - Persistencia más completa del estado de flujo.
   - Salidas pensadas para uso real desde Codex.

2. Mejorar documentación de uso.
   - Ampliar ejemplos reales de invocación.
   - Añadir troubleshooting de instalación si aparece en nuevas máquinas.
   - Qué garantías existen y cuáles no.

## Siguiente Fase: UX Operativa Codex

- Crear scripts Codex-native para arrancar y continuar flujos.
- Sincronizar estado con documentos operativos bajo `docs/project/`.
- Añadir ejemplos reales de uso para `quick`, `fix` y `feature`.
- Documentar claramente cómo se trabaja sin slash commands Claude.

## Fase de Memoria

- Ampliar MCP hacia paridad parcial con Alfred Dev:
  - commits;
  - enlaces entre decisiones;
  - health checks;
  - export/import;
  - ADRs;
  - timeline por iteración.
- Añadir migración opcional desde memorias antiguas de Alfred Dev.
- Añadir retención, limpieza y compactación.

## Fase de Orquestación

- Sustituir las antiguas suposiciones de `Agent` de Claude por primitivas reales de Codex cuando estén claras.
- Crear recursos explícitos para roles:
  - product-owner;
  - architect;
  - senior-dev;
  - qa-engineer;
  - security-officer;
  - tech-writer;
  - devops-engineer;
  - especialistas opcionales.
- Mejorar autopilot con reglas de aprobación y parada más finas.

## Fase de Hooks o Alternativas

- Validar si Codex ofrece hooks o eventos equivalentes.
- Si existen, portar solo equivalentes seguros:
  - bootstrap;
  - captura de evidencia;
  - gates;
  - memoria;
  - cierre de sesión.
- Si no existen, mantener un modelo explícito basado en helpers y documentar la pérdida de garantías.

## Fase de Release

- Añadir pruebas de integración sobre un proyecto desechable.
- Añadir auditoría de release.
- Añadir control de versión y changelog.
- Crear instalación documentada y repetible.
- Publicar como plugin instalable cuando el flujo marketplace esté verificado.

## Fuera de Alcance por Ahora

- Paridad total con Alfred Dev.
- Slash commands Claude.
- Hooks Claude.
- `${CLAUDE_PLUGIN_ROOT}`.
- `Agent` tool de Claude.
- Selina visual completa.
- SonarQube/Docker automatizado.
