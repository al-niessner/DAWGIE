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
An example of how to use the endpoint with curl including its output. All examples are done using an instance of exercise, which is created by running the `Coda/exercise/run.sh` script and the entire JSON object is shown not just `content`.

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
- [`/api/pipeline/state`](#/apipipelinestate-get)
- [`/api/rev/current`](#/api/rev/current-get)
- [`/api/rev/submit`](#/api/rev/submit-get)
- [`/api/schedule/doing`](#/api/schedule/doing-get)
- [`/api/schedule/failed`](#/api/schedule/failed-get)
- [`/api/schedule/in-progress`](#/api/schedule/in-progress-get)
- [`/api/schedule/stats`](#/api/schedule/stats-get)
- [`/api/schedule/succeeded`](#/api/schedule/succeeded-get)
- [`/api/schedule/to-do`](#/api/schedule/to-do-get)

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
Retrieve run statistics about a node in the data flow model.
#### Parameters
- node_name : the name task.algorithm for which to collect the statistics
#### Content
A JSON object where all keys can be missing which indicate default values of "unknown" for status or "-" for runid and date should be used.
```
{
  "date"   : "last completion UTC",
  "runid"  : <integer of last runid>,
  "status" : "both"|"failed"|"processing"|"scheduled"|"succeeded"
}
```
#### Example
```
curl -ksX GET 'https://localhost:8080/api/df_model/statistics?node_name=disk.engine | jq'
```
```
{
  "content": {
    "status": "scheduled"
  },
  "message": "",
  "status": "success"
}
```

Then sometime later...

```
curl -ksX GET 'https://localhost:8080/api/df_model/statistics?node_name=disk.engine | jq'
```
```
{
  "content": {
    "date": "2026-01-22 18:42:50.375502+00:00",
    "runid": 1,
    "status": "succeeded"
  },
  "message": "",
  "status": "success"
}
```
### `/api/logs/recent` (GET)
#### Description
Retrieve the logs from the pipelines memory. The pipeline keeps track of logged messages for some configurable amount defined by `dawgie.context.log_capacity` that defaults to 100 messages of `dawgie.context.log_level` or higher. These messages do not include those generated by workers. For full logs, the server plus workers, see the log file.
#### Parameters
- _levels_ : the desired levels in a comma separated list with full list being `debug,info,warning,error,critical`.
- _limit_ : the number of messages to return with 0 or not being given to mean the pipeline's entire memory.
#### Content
A JSON list of the messages with the smallest index of the list the newest message. In other words, a JSON list sorted in time descending order.
#### Example
```
curl -ksX GET 'https://localhost:8080/api/logs/recent?limit=3' | jq
```
```
{
  "content": [
    {
      "timeStamp": "2026-01-22 10:20:36,400",
      "name": "dawgie.pl.farm",
      "level": "CRITICAL",
      "message": "New run ID (3) for algorithm feedback.sensor trigger by the event: following feedback loop"
    },
    {
      "timeStamp": "2026-01-22 10:19:56,399",
      "name": "dawgie.pl.farm",
      "level": "CRITICAL",
      "message": "New run ID (2) for algorithm feedback.command trigger by the event: command-run requested by user"
    },
    {
      "timeStamp": "2026-01-22 10:19:46,398",
      "name": "dawgie.pl.farm",
      "level": "CRITICAL",
      "message": "New run ID (1) for algorithm network.analyzer trigger by the event: New software changeset FAKE-VERSION-FOR-EXERCISE"
    }
  ],
  "message": "",
  "status": "success"
}
```
```
curl -ksX GET 'https://localhost:8080/api/logs/recent?levels=critical,info&limit=3' | jq
```
```
{
  "content": [
    {
      "timeStamp": "2026-01-22 10:19:41,397",
      "name": "transitions.core",
      "level": "INFO",
      "message": "Executed callback 'start'"
    },
    {
      "timeStamp": "2026-01-22 10:19:41,397",
      "name": "dawgie.pl.state",
      "level": "INFO",
      "message": "exiting state starting"
    },
    {
      "timeStamp": "2026-01-22 10:19:41,396",
      "name": "dawgie.pl.state",
      "level": "INFO",
      "message": "Starting the pipeline"
    }
  ],
  "message": "",
  "status": "success"
}
```
### `/api/pipeline/state` (GET)
#### Description
Return the current state of the pipeline.
#### Parameters
_None_
#### Content
A JSON object with the following information:
```
{
    "name"   : "archiving"|"contemplation"|"gitting"|"loading"|"running"|"starting"| "updating",
    "ready"  : false|true,
    "status" : "active"|"entering"|"exiting"
}
```
Where `ready` means the pipeline is ready to do work.
#### Example
```
curl -ksX GET 'https://localhost:8080/api/pipeline/state' | jq
```
```
{
  "content": {
    "name": "running",
    "ready": true,
    "status": "active"
  },
  "message": "",
  "status": "success"
}
```
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
A JSON object with the following content:
```
```
#### Example
```
curl -ksX GET 'https://localhost:8080/api/schedule/stats' | jq
```
```
{
  "content": {
    "jobs": {
      "doing": 1,
      "todo": 1
    },
    "workers": {
      "busy": 0,
      "idle": 2
    }
  },
  "message": "",
  "status": "success"
}
```
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
Return statistics about the schedule and workers to get it done.
#### Parameters
_None_
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

