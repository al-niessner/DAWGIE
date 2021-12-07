# REST API

Describes the REST API (endpoints) that DAWGIE provides to access the data it manages. Inputs to the REST API are mostly if not all URL parameters. The outputs are JSON or text.

Each endpoint begins with `/app`, short for application, to identify the REST API that can be programatically accessed. These endpoints are different than the endpoints that return fixed pages like /pages/index.html that is the front page. The endpoints are then further subdivided into logical groups: `/app/db`, `/app/filter`, `/app/pl`, `/app/schedule`, `/app/search`. There are several endpoints that do not fall into these logical groups as well.

- `/app/db` direct access to the data keys (target names, task names, etc)
- `/app/filter` restrict searches in the data base
- `/app/pl` direct access to information about the state of the piupeline
- `/app/schedule` direct access to the schedule as DAWGIE currently understands it
- `/app/search` search the database to select specific data keys (target names, task names, etc)

The endpoints are listed in alphabetical order and documented as:

---

## Endpoint (GET/POST)
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

## TOC

- ['/app/changeset.txt'](#appchangesettxt-get)
- ['/app/db/item'](#appdbitem-get)
- ['/app/db/lockview'](#appdblockview-get)
- ['/app/db/prime'](#appdbprime-get)
- ['/app/db/targets'](#appdbtargets-get)
- ['/app/db/versions'](#appdbversions-get)
- ['/app/filter/admin'](#appfilteradmin-get)
- ['/app/filter/dev'](#appfilterdev-get)
- ['/app/filter/user'](#appfilteruser-get)
- ['/app/pl/log'](#apppllog-get)
- ['/app/pl/state'](#appplstate-get)
- ['/app/run'](#apprun') , [HttpMethod.POST]
- ['app/schedule/crew-get'](#ppschedulecrew-get-get)
- ['/app/schedule/doing'](#appscheduledoing-get)
- ['/app/schedule/events'](#appscheduleevents-get)
- ['/app/schedule/failure'](#appschedulefailure-get)
- ['/app/schedule/success'](#appschedulesuccess-get)
- ['/app/schedule/tasks'](#appscheduletasks-get)
- ['/app/schedule/todo'](#appscheduletodo-get)
- ['/app/search/completion/sv'](#appsearchcompletion/sv-get)
- ['/app/search/completion/tn'](#appsearchcompletion/tn-get)
- ['/app/search/ri'](#appsearchri-get)
- ['/app/search/sv'](#appsearchsv-get)
- ['/app/search/tn'](#appsearchtn-get)
- ['/app/state/status'](#appstatestatus-get)
- ['/app/submit'](#appsubmit') , [HttpMethod.POST]
- ['app/versions'](#ppversions-get')


## `app/changeset.txt` (GET-get)
'/app/db/item'
'/app/db/lockview'
'/app/db/prime'
'/app/db/targets'
'/app/db/versions'
'/app/filter/admin'
'/app/filter/dev'
'/app/filter/user'
'/app/pl/log'
'/app/pl/state'
'/app/run', [HttpMethod.POST]
'/app/schedule/crew'
'/app/schedule/doing'
'/app/schedule/events'
'/app/schedule/failure'
'/app/schedule/success'
'/app/schedule/tasks'
'/app/schedule/todo'
'/app/search/completion/sv'
'/app/search/completion/tn'
'/app/search/ri'
'/app/search/sv'
'/app/search/tn'
'/app/state/status'
'/app/submit', [HttpMethod.POST]
'/app/versions'
