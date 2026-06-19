# REST API

Describes the REST API (endpoints) that DAWGIE provides to access the data it manages. Inputs to the REST API are mostly if not all URL parameters. The outputs are HTML, JSON or text depending on the endpoint.

Each endpoint begins with `/app`, short for application, to identify the REST API that can be programatically accessed. These endpoints are different than the endpoints that return fixed pages like /pages/index.html that is the front page. The endpoints are then further subdivided into logical groups: `/app/db`, `/app/filter`, `/app/pl`, `/app/schedule`, `/app/search`. There are several endpoints that do not fall into these logical groups as well.

- `/app/db` direct access to the data keys (target names, task names, etc)
- `/app/filter` restrict searches in the data base
- `/app/pl` direct access to information about the state of the piupeline
- `/app/schedule` direct access to the schedule as DAWGIE currently understands it
- `/app/search` search the database to select specific data keys (target names, task names, etc)

The endpoints are listed in alphabetical order and documented as:

---

## Endpoint (GET/POST) (HTML/JSON/text)
### Description
actual description

### Inputs
- varname:type  
  description

### Outputs
- varname:type  
  description
    
### Example

```
curl command
and results
```

---


"""Note: all examples are using the Algorithm Engine (AE) defined in DAWGIE/Test/ae"""

## TOC

- [`/app/changeset.txt`](#appchangesettxt-get-text)
- [`/app/db/item`](#appdbitem-get-html)
- [`/app/db/lockview`](#appdblockview-get)
- [`/app/db/prime`](#appdbprime-get)
- [`/app/db/targets`](#appdbtargets-get)
- [`/app/db/versions`](#appdbversions-get)
- [`/app/filter/admin`](#appfilteradmin-get)
- [`/app/filter/dev`](#appfilterdev-get)
- [`/app/filter/user`](#appfilteruser-get)
- [`/app/pl/log`](#apppllog-get)
- [`/app/pl/state`](#appplstate-get)
- [`/app/run`](#apprun-post)
- [`app/schedule/crew-get`](#ppschedulecrew-get-get)
- [`/app/schedule/doing`](#appscheduledoing-get)
- [`/app/schedule/events`](#appscheduleevents-get)
- [`/app/schedule/failure`](#appschedulefailure-get)
- [`/app/schedule/success`](#appschedulesuccess-get)
- [`/app/schedule/tasks`](#appscheduletasks-get)
- [`/app/schedule/todo`](#appscheduletodo-get)
- [`/app/search/completion/sv`](#appsearchcompletion/sv-get)
- [`/app/search/completion/tn`](#appsearchcompletion/tn-get)
- [`/app/search/ri`](#appsearchri-get)
- [`/app/search/sv`](#appsearchsv-get)
- [`/app/search/tn`](#appsearchtn-get)
- [`/app/state/status`](#appstatestatus-get)
- [`/app/submit`](#appsubmit-post)
- [`app/versions`](#ppversions-get`)


## `/app/changeset.txt` (GET) (text)
### Description

Returns the GIT changeset ID of the Algorithm Engine (AE) -- aka science code -- that this server is using.

### Inputs

_no inputs_

### Outputs

- _unnamed_:string  
  the GIT changeset ID

### Example

```
curl -X GET "<URL base>/app/changeset.txt"
e716cd9eb32ce97653112d8bc8be140357085f58
```

## `/app/db/item` (GET) (html)
### Description

Render a specific state vector to HTML.

### Inputs

- path:string  
  '.' separate complete name of a state vector.

### Outputs
 - _unnamed_:string  
   a complete HTML page

### Example

```
curl -X GET "<URL base>/app/db/item?path="
abc
```

## `/app/db/lockview` (GET)
### Description
### Inputs
### Outputs
### Example

```
curl -X GET "<URL base>/app/db/lockview"
abc
```

## `/app/db/prime` (GET)
### Description
### Inputs
### Outputs
### Example

```
curl -X GET "<URL base>/app/db/prime"
abc
```

## `/app/db/targets` (GET)
### Description
### Inputs
### Outputs
### Example

```
curl -X GET "<URL base>/app/db/targets"
abc
```

## `/app/db/versions` (GET)
### Description
### Inputs
### Outputs
### Example

```
curl -X GET "<URL base>/app/db/versions"
abc
```

## `/app/filter/admin` (GET)
### Description
### Inputs
### Outputs
### Example

```
curl -X GET "<URL base>/app/filter/admin"
abc
```

## `/app/filter/dev` (GET)
### Description
### Inputs
### Outputs
### Example

```
curl -X GET "<URL base>/app/filter/dev"
abc
```

## `/app/filter/user` (GET)
### Description
### Inputs
### Outputs
### Example

```
curl -X GET "<URL base>/app/filter/user"
abc
```

## `/app/pl/log` (GET)
### Description
### Inputs
### Outputs
### Example

```
curl -X GET "<URL base>/app/pl/log"
abc
```

## `/app/pl/state` (GET)
### Description

Returns the current state of the pipeline FSM

### Inputs

None

### Outputs

JSON object:
- name: current state
- ready: boolean indicating that the pipeline is ready to do work
- status: active/entering/exiting

### Example

```
curl -X GET "<URL base>/app/pl/state"
{
  "name": "running",
  "ready": true,
  "status": "active"
}
```

## `/app/run`, (POST)
### Description

Tells the scheduler to move the given targets and tasks into the TODO list. Every target will be run for every teask given. For instance:

`target=a,target=b,target=c,task=g.h`

means schedule targets a, b, and c for task g and algorithm h to run as soon as possible.

`target=a,target=b,target=c,task=g.h,task=j.k`

means schedule targets a, b, and c for task.alg g.h and task.alg j.k.

### Inputs

- targets: one or more valid targets. The special target `__all__` will be translated into an alphabetical list of all know targets for non aspect algorithms.
- tasks: one or more valid task.algorithms to execute.

### Outputs

JSON object representing the success of the request.

- alert_status: "success" when it works and "failed" when it does not.
- alert_message: human readable detail of why success/failed.

### Example

```
curl -X POST "<URL base>/app/run?target=G,task=a.b"
{"alert_status": "success", "alert_message": "All jobs scheduled to run."}
```

## `/app/schedule/crew` (GET)
### Description

Reports back what part of the schedule the work crew is currently busy accomplishing.

### Inputs

None

### Outputs

JSON object that contains a busy list and the number of workers in the crew that are idle.

- busy: each JSON string in the list represents a busy crew member. It states what task is being processed and how long they have been doing the task.
- idle: the number of workers that need a task

### Example

```
curl -X GET "<URL base>/app/schedule/crew"
{
  "busy": [
    "data.collect[WASP-90] duration: 137:33:07",
    "data.collect[WASP-81] duration: 137:30:22",
    "data.calibration[L 98-59] duration: 67:10:02",
    "cerberus.atmos[TOI-178] duration: 42:42:07",
    "cerberus.atmos[TOI-1136] duration: 42:38:32",
    "cerberus.atmos[TRAPPIST-1] duration: 41:07:22"
  ],
  "idle": "124"
}
```

## `/app/schedule/doing` (GET)
### Description
### Inputs
### Outputs
### Example

```
curl -X GET "<URL base>/app/schedule/doing"
abc
```

## `/app/schedule/events` (GET)
### Description
### Inputs
### Outputs
### Example

```
curl -X GET "<URL base>/app/schedule/events"
abc
```

## `/app/schedule/failure` (GET)
### Description
### Inputs
### Outputs
### Example

```
curl -X GET "<URL base>/app/schedule/failure"
abc
```

## `/app/schedule/success` (GET)
### Description
### Inputs
### Outputs
### Example

```
curl -X GET "<URL base>/app/schedule/success"
abc
```

## `/app/schedule/tasks` (GET)
### Description
### Inputs
### Outputs
### Example

```
curl -X GET "<URL base>/app/schedule/tasks"
abc
```

## `/app/schedule/todo` (GET)
### Description
### Inputs
### Outputs
### Example

```
curl -X GET "<URL base>/app/schedule/todo"
abc
```

## `/app/search/completion/sv` (GET)
### Description
### Inputs
### Outputs
### Example

```
curl -X GET "<URL base>/app/search/completion/sv"
abc
```

## `/app/search/completion/tn` (GET)
### Description
### Inputs
### Outputs
### Example

```
curl -X GET "<URL base>/app/search/completion/tn"
abc
```

## `/app/search/ri` (GET)
### Description
### Inputs
### Outputs
### Example

```
curl -X GET "<URL base>/app/search/ri"
abc
```

## `/app/search/sv` (GET)
### Description
### Inputs
### Outputs
### Example

```
curl -X GET "<URL base>/app/search/sv"
abc
```

## `/app/search/tn` (GET)
### Description
### Inputs
### Outputs
### Example

```
curl -X GET "<URL base>/app/search/tn"
abc
```

## `/app/state/status` (GET)
### Description
** DEPRECATED **

use /app/pl/state

### Inputs
### Outputs
### Example

```
curl -X GET "<URL base>/app/state/status"
abc
```

## `/app/submit` (POST)
### Description
### Inputs
### Outputs
### Example

```
curl -X POST "<URL base>/app/submit"
abc
```

## `/app/versions` (GET)
### Description
### Inputs
### Outputs
### Example

```
curl -X GET "<URL base>/app/versions"
abc
```

