# REST API

Describes the REST API (endpoints) that DAWGIE provides to access the data it manages. Inputs to the REST API are mostly if not all URL parameters. The outputs are always JSON. The endpoints are documented as:


## Endpoint (Get/Post)
__Description__
> actual description

__Inputs__
- varname:type description

__Outputs__
- varname:type description
    
__Example__

```
curl command
and results
```

Each endpoint begins with `/app`, short for application, to identify the REST API that can be programatically accessed. These endpoints are different than the endpoints that return fixed pages like /pages/index.html that is the front page. The endpoints are then further subdivided into logical groups: `/app/db`, `/app/filter`, `/app/pl`, `/app/schedule`, `/app/search`. There are several endpoints that do not fall into these logical groups as well.

- `/app/db` direct access to the data keys (target names, task names, etc)
- `/app/filter` restrict searches in the data base
- `/app/pl` direct access to information about the state of the piupeline
- `/app/schedule` direct access to the schedule as DAWGIE currently understands it
- `/app/search` search the database to select specific data keys (target names, task names, etc)
