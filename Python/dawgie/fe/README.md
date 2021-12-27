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
### Inputs
### Outputs
### Example

```
curl -X GET "<URL base>/app/pl/state"
abc
```

## `/app/run`, (POST)
### Description
### Inputs
### Outputs
### Example

```
curl -X POST "<URL base>/app/run"
abc
```

## `/app/schedule/crew` (GET)
### Description
### Inputs
### Outputs
### Example

```
curl -X GET "<URL base>/app/schedule/crew"
abc
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

