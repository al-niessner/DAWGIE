# API Documentation


## Endpoints

DAWGIE front end (FE) endpoints do not use HTTP status codes. If the status code is not 200, then it is a real connection problem and not an FE problem.

FE endpoints all return the same JSON object:
```
{
    "content" : <endpoint specific>,
    "message" : "string of why/how things went awry",
    "status"  : "error"|"failure"|"success"
}
```

When `status` is `success`, the value of `content` will be valid and `message` is undefined. Each endpoint returns different `content` and is described in the endpoint documentation.

When `status` is `failure`, the value of `message` will be a string attempting to explain why/how the failure occurred and prevented the request from being completed successfully. The value of `content` will be an UTC date and time string to align this message with the log file contents for further illuminating the problem that occurred.

When `status` is `error`, the value of `message` will be the exception message. The value of `content` will be an UTC date and time string to align this message with teh log file contents where the full stack trace can be found.

Each endpoint will be detailed with the following information:
### `/api/unit/request` (GET|PUSH|PUT)
#### Description
A brief description of endpiont.
#### Parameters
A list of allowable paraemters and if they are optional
#### Content
A description of `content` for a successful request of the endpoint. Will included JSON examples.
#### Example
An example of how to use the endpoint with curl including its output. All examples are done using an instance of exercise, which is created by running the `Coda/exercise/run.sh` script.

- [`/api/ae/name`](#apiaename-get)
- [`/api/cmd/run`](#/api/cmd/run-get)
- [`/api/database/search`](#/api/database/search-get)
- [`/api/database/search/runid`](#/api/database/search/runid-get)
- [`/api/database/search/target`](#/api/database/search/target-get)
- [`/api/database/search/task`](#/api/database/search/task-get)
- [`/api/database/search/alg`](#/api/database/search/alg-get)
- [`/api/database/search/sv`](#/api/database/search/sv-get)
- [`/api/database/search/val`](#/api/database/search/val-get)
- [`/api/database/view`](#/api/database/view-get)
- [`/api/df_model/statistics`](#/api/df_model/statistics-get)
- [`/api/logs/recent?limit=3`](#/api/logs/recent?limit=3-get)
- [`/api/rev/current`](#/api/rev/current-get)
- [`/api/rev/submit`](#/api/rev/submit-get)
- [`/api/schedule/doing`](#/api/schedule/doing-get)
- [`/api/schedule/failed`](#/api/schedule/failed-get)
- [`/api/schedule/in-progress`](#/api/schedule/in-progress-get)
- [`/api/schedule/stats`](#/api/schedule/stats-get)
- [`/api/schedule/succeeded`](#/api/schedule/succeeded-get)
- [`/api/schedule/to-do`](#/api/schedule/to-do-get)
- [`/api/state/pipeline`](#/api/state/pipeline-get)

### `/api/ae/name` (GET)
#### Description
DAWGIE is an agent that organizes and managers to workers to accomplish tasks defined by the AE. This endpoint returns the name of the AE, which is defined in dawgie.context.ae_base_package.
#### Parameters
_None_
#### Content
String representation of the AE name.
#### Example
```
curl -ksX GET 'https://localhost:8080/api/ae/name' | jq
```
```
{
  "content": "ae",
  "message": "",
  "status": "success"
}
```
### `/api/cmd/run` (GET)
#### Description
#### Parameters
#### Content
#### Example
### `/api/database/search` (GET)
#### Description
#### Parameters
#### Content
#### Example
### `/api/database/search/runid`  --> no params returns max value (GET)
#### Description
#### Parameters
#### Content
#### Example
### `/api/database/search/target` --> no params returns full list (GET)
#### Description
#### Parameters
#### Content
#### Example
### `/api/database/search/task` --> no params returns full list (GET)
#### Description
#### Parameters
#### Content
#### Example
### `/api/database/search/alg` --> no params returns full list (GET)
#### Description
#### Parameters
#### Content
#### Example
### `/api/database/search/sv` --> no params returns full list (GET)
#### Description
#### Parameters
#### Content
#### Example
### `/api/database/search/val` --> no params returns full list (GET)
#### Description
#### Parameters
#### Content
#### Example
### `/api/df_model/statistics` (GET)
#### Description
#### Parameters
#### Content
#### Example
### `/api/logs/recent?limit=3` (GET)
#### Description
#### Parameters
#### Content
#### Example
### `/api/rev/current` (GET)
#### Description
#### Parameters
#### Content
#### Example
### `/api/rev/submit` (GET)
#### Description
#### Parameters
#### Content
#### Example
### `/api/schedule/doing` (GET)
#### Description
#### Parameters
#### Content
#### Example
### `/api/schedule/failed` (GET)
#### Description
#### Parameters
#### Content
#### Example
### `/api/schedule/in-progress` (GET)
#### Description
#### Parameters
#### Content
#### Example
### `/api/schedule/stats` (GET)
#### Description
#### Parameters
#### Content
#### Example
### `/api/schedule/succeeded` (GET)
#### Description
#### Parameters
#### Content
#### Example
### `/api/schedule/to-do` (GET)
#### Description
#### Parameters
#### Content
#### Example
### `/api/state/pipeline` (GET)
#### Description
#### Parameters
#### Content
#### Example
