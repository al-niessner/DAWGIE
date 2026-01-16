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

`/api/ae/name`
`/api/cmd/run`
`/api/database/search`
`/api/database/search/runid`  --> no params returns max value
`/api/database/search/target` --> no params returns full list
`/api/database/search/task` --> no params returns full list
`/api/database/search/alg` --> no params returns full list
`/api/database/search/sv` --> no params returns full list
`/api/database/search/val` --> no params returns full list
`/api/database/view`  --> given a full name, generate its view
`/api/df_model/statistics`
`/api/logs/recent?limit=3`
`/api/rev/current`
`/api/rev/submit`
`/api/schedule/doing`
`/api/schedule/failed`
`/api/schedule/in-progress`
`/api/schedule/stats`
`/api/schedule/succeeded`
`/api/schedule/to-do`
`/api/state/pipeline`

`/api/ae/name`
#### Description
#### Parameters
#### Content
#### Example
`/api/cmd/run`
#### Description
#### Parameters
#### Content
#### Example
`/api/database/search`
#### Description
#### Parameters
#### Content
#### Example
`/api/database/search/runid`  --> no params returns max value
#### Description
#### Parameters
#### Content
#### Example
`/api/database/search/target` --> no params returns full list
#### Description
#### Parameters
#### Content
#### Example
`/api/database/search/task` --> no params returns full list
#### Description
#### Parameters
#### Content
#### Example
`/api/database/search/alg` --> no params returns full list
#### Description
#### Parameters
#### Content
#### Example
`/api/database/search/sv` --> no params returns full list
#### Description
#### Parameters
#### Content
#### Example
`/api/database/search/val` --> no params returns full list
#### Description
#### Parameters
#### Content
#### Example
`/api/df_model/statistics`
#### Description
#### Parameters
#### Content
#### Example
`/api/logs/recent?limit=3`
#### Description
#### Parameters
#### Content
#### Example
`/api/rev/current`
#### Description
#### Parameters
#### Content
#### Example
`/api/rev/submit`
#### Description
#### Parameters
#### Content
#### Example
`/api/schedule/doing`
#### Description
#### Parameters
#### Content
#### Example
`/api/schedule/failed`
#### Description
#### Parameters
#### Content
#### Example
`/api/schedule/in-progress`
#### Description
#### Parameters
#### Content
#### Example
`/api/schedule/stats`
#### Description
#### Parameters
#### Content
#### Example
`/api/schedule/succeeded`
#### Description
#### Parameters
#### Content
#### Example
`/api/schedule/to-do`
#### Description
#### Parameters
#### Content
#### Example
`/api/state/pipeline`
#### Description
#### Parameters
#### Content
#### Example
