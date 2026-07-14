# Внедрить `goal-brainstorm`

## Outcome

Добавить в plugin `workflow-container-tools` generic skill `goal-brainstorm`, который согласует и изменяет правильные instruction/design/specification owners, создаёт один dated goal-файл и опционально активирует persistent goal после отдельного подтверждения. После проверки replacement workflow удалить устаревшие documentation trees и локальный Superpowers plugin.

## Source Contracts

- `doc/spec/2026-07-14-goal-brainstorm.md`: полный целевой контракт skill, интеграции, миграции и acceptance criteria.
- `AGENTS.md`: ограничения repository `workflow-container-developer` и plugin ownership.
- `/home/andrey/Projects/marketplace-tr-priority/AGENTS.md`: действующие repository constraints и устаревшие правила, которые спецификация требует удалить.

## Constraints

Считать перечисленные source contracts единственными владельцами требований. Не создавать implementation plan, compatibility bridge, автоматический commit или скрытую goal activation. Сохранять несвязанные изменения во всех затронутых repositories.

## Verification

Выполнить все acceptance criteria из `doc/spec/2026-07-14-goal-brainstorm.md`, применимые repository checks и semantic review итогового diff. До завершения удалить найденные дубли, лишние wrappers, размазанную ответственность, противоречия и остатки удаляемого lifecycle.
