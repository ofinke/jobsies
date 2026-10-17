You can add charts to the **Trends** page by setting `output_monitoring` in a Jobsie definition. Enter the value as JSON in the definition form, or provide it when creating or updating a definition through the API.

For example, this configuration charts the `number` field from the latest 30 successful executions:

```json
{
  "version": 1,
  "monitors": [
    {
      "title": "Number",
      "field": "/number",
      "visualization": "line",
      "window": {
        "type": "last_executions",
        "count": 30
      }
    }
  ]
}
```

Each item in `monitors` defines one chart:

- `title` is the chart title.
- `field` is a [JSON Pointer](https://www.rfc-editor.org/rfc/rfc6901) to a value in the Jobsie output. It starts with `/`; for example, `/number` refers to the top-level `number` field.
- `visualization` is currently `line`.
- `window` selects which executions to include. Use `last_executions` and set `count` to a positive number.
- `unit` is optional and is displayed alongside the values.

You can add more objects to `monitors` to display multiple charts for the same Jobsie. Values must be finite numbers to appear in a chart; missing fields and non-numeric values are shown as gaps. Set `monitors` to an empty list (or leave `output_monitoring` empty) if you do not want charts for that Jobsie.
