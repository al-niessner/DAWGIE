# Pipeline NTR (50482)
## Prior Art
49811

## Title
Data and Algorithm Work-flow Generation, Introspection, and Execution (DAWGIE)

## Contributors:
- Al Niessner
- Kevin Ortega
- Yi Yuan

## Software Description
### Abstract
*The abstract should focus on the programmatic and/or utilization aspects of the software*

The pipeline manager and persistence elements of the NTR 49811 framework elements organize work-flow, schedule, and distribute jobs across compute nodes. It also prepares, delivers, and receives the data the job requires then provides. Traditionally, the work-flow, schedule, distribution plan, data collection, and results take significant effort. In the case of this software, it is all done immediately at run-time from ANY science developed software conforming to the NTR 49811 framework.

### Problem Statement
*What problems are you trying to solve in the software?*

DAWGIE is an implementation of NTR 49811 framework elements pipeline management and persistence. NTR 49811 framework defines the concepts of anonymous data, persisting the data, and perform distributed processing that the pipeline manager and persistence elements must implement.

Anonymous data is simple to require but not always easy to implement because the pipeline must route data among the framework elements and yet have no knowledge of the data itself. The framework helps the anonymity and routing with the definitions of *StateVector* and *Value* but leaves the complete definition of the anonymous data to pipeline management and persistence. The problem for the pipeline management and persistence is to complete the definitions without creating a dependency between the pipeline management and persistence elements and the algorithm engine element.

Data persistence is required save and recover anonymous as the various framework elements evolve. It must also signal to the pipeline manager that the anonymous blob being saved is unique within the scope that it was created. Retrieval and uniqueness are the difficult problems for persistence to solve.

The work required by the algorithm engine element of the framework can be quite extensive requiring the pipeline manager to distribute the processing among one to many computation nodes. Actual distribution is not the most difficult problem for the pipeline manager. Building the work flow, which work needs to be done, and scheduling it is significantly more difficult.

### Accomplishes
*This software accomplishes the following?*

The DAWGIE software accomplishes an implementation of the primary concepts imposed by the NTR 49811 framework: anonymous data, data persistence, and pipeline management.

Data anonymity is required by the framework because the implementation DAWGIE is independent of the Algorithm Engine element of the framework. The framework allows DAWGIE to identify the author of the data through naming and version even though DAWGIE as no knowledge of the data itself. Because the language of the framework and further implementations is Python, DAWGIE forces a further requirement on the data that it be "pickle-able". The additional requirement was accepted by the framework and pushed to the Algorithm Engine element. DAWGIE uses a lazy load implementation -- loaded only when an Algorithm Engine sub-element requests data from a specific author -- to remove routing and, thus, requiring knowledge about the data itself.

Data persistence has two independent implementations. In the case of small and simple data author relationships, the Python shelve module is used for persistence. As the number of unique authors grows, the relations grow faster (non-linear) and requires a more sophisticated persistence tool. In the latter case, postgresql is used for persistence. Both implementations are the design making them quickly interchangeable. Neither actually store the data blobs themselves. They -- shelve and postgresql -- only store the author's unique ID -- name and version -- and then reference the blob on disk. Using the relational DB proprieties of shelve (Python dictionaries) and postgresql (relational DB) any request for data from a specific author can quickly be resolved. Creating unique names for all of the data blobs is achieved using {md5 hash}_{sha1 hash}. These names also allow the persistence to recognize if the data is already known.

For pipeline management, DAWGIE implements a worker farm, a work flow Abstract Syntax Tree (AST), and signaling from data persistence to execute the tasks within the framework Algorithm Engine element. The data persistence implementation signals the pipeline management element when new data has been authored. The manager searches the AST for all tasks that depend on the author and schedules all tasks that depend on the author starting with the earliest dependent. The new data signals can be generated at the end any task. When a task moves from being scheduled to executing, the foreman of the worker farm passes the task to a waiting worker on a compute node. The worker then loads the data via data persistence for the task and begins executing the task. Upon completion of the task, the worker saves the data via data persistence and notifies the foreman it is ready for another task. In this fashion, DAWGIE walks the minimum and complete nodes in the AST that depend on any new data that has been generated. The pipeline management offers periodic tasks as well that treat a temporal event as new data.

- anonymize data
  - picklable
  - lazy loading to avoid routing
  - name
  - version
- data persistence
  - retrieve data
  - determine uniqueness
- processing distribution (pipeline management)
  - worker farm
  - reflection to build AST
  - persistence flags unique data

### Features
*What are the unique features of the software?*

Automated work flow determination and execution is the unique feature of DAWGIE. Rather than expending months to years of determining work flow and external dependencies followed with months of scheduling when to build products relative to all dependencies, DAWGIE uses architecture, design, and reflection to determine all of these at run-time and then operate on them directly.

Data event processing is also a unique feature of DAWGIE. While similar software will wait for data then blindly process, DAWGIE identifies new data and reacts to that event accordingly. Wrapped within the data event is most unique feature, DAWGIE is able to identify new data. Because the data is anonymous, it makes identifying new data more powerful but does not add to its uniqueness.

- determine uniqueness
- reflection to build AST
- data driven processing
- uniqueness to generated events

### Improvements
*What improvements have been made over existing similar software application?*

Traditional Science Data Systems (SDS) for missions like SMAP, SWOT, NISAR, EcoSTRESS, and more all use system engineers to build artifacts called products. All of the inputs for these products are determined over extended periods of time -- scale of years -- only to be changed at the last moment as the instrument, environment, and actual data processing come to realization. DAWGIE foregoes all of the system engineering work for having an Algorithm Development Team (ADT) -- more commonly the science team -- develop their algorithm within the context of an architecture and then use reflection to short-cut work flow determination and execution to seconds.

- traditionally work flow predetermined 
- traditionally uniqueness is indeterminate

### Explanation
*Does your work relate to current or future NASA (include reimbursable) work that has value to the conduct of aeronautical and space activities?*

## Outside Interest
### Advantage
*What advantages does this software have over existing software?*

### Commercial Applications
*Are there any known commercial applications? What are they? What else is currently on the market that is similar?*

### Interest
*Is anyone interested in the software? Who? Please list organization names and contact information.*

### System Requirements
*What are the current hardware and operating system requirements to run the software? (Platform, RAM requirement, special equipment, etc.)*
