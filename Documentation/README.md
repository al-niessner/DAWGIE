# Table of Contents
* [Concept NTR](#concept-ntr-49811)
* [AE NTR](#algorithm-engine-ntr)
* [Aspect NTR](#aspect-ntr)
* [Persistence NTR](#persistence-ntr)
* [Pipeline NTR](#pipeline-ntr)

# Concept NTR 49811
## Title
Uniform spectral processing of multiple transiting exoplanets.

## Contributors:
- Al Niessner
- Mark Swain

## Software Description
### Abstract
*The abstract should focus on the programmatic and/or utilization aspects of the software...*

The architecture, design, and resulting framework implementation presented in this NTR creates four independent systems: algorithm engine, aspects, persistence, and pipeline management. The framework implementation is in Python and uses the Facade Pattern to keep the four systems independent and plugable. It uses the reflective nature of Python classes and types along with interfaces to keep data types from generating unwanted dependencies between the systems.


### Problem Statement
There are currently tens of transiting exoplanets (targets) that have an observed spectra and then analyzed. The methods and algorithms currently employed for the spectral analysis vary greatly for many reasons like the team that collected the data, the telescope and instrument (source) that collected the data, or the state art of understanding at the time it was processed. Also, the current state of the art methods and algorithms are very man-effort intensive making it prohibitive to process numerous targets let alone processes disparate sources uniformly.

The belief is that there is significant science to be discovered through a uniform analysis  of the available targets. Thus, the problem being addressed is, how does one uniformly process the spectral data of multiple targets using state of the art methods and algorithms with the intent to analyze common aspects of the various targets to reveal interesting science while divorcing the man-effort from the number of targets processed. 

### Accomplishes
*This software accomplishes the following?*

#### Outline
1. Isolates the pipeline processor from the science algorithm
   1. Accommodate state of the art changes or various users (projects)
   2. Allow for independent development of the pipeline control and science algorithm
2. Work flow is determined at run time
   1. Inexpensive as state of the art changes
   2. Refactoring is inexpensive
   3. Manifold at the input to transform sources for uniform processing
   4. Reduces computational needs via
      1. versions found at run time when discovering work flow
      2. file naming convention for data versions
3. State vector representation
   1. Inexpensive adding new algorithmic elements
   2. Allows for aspect analysis
   3. Allows for AI to translate into probability of interest
4. Data storage (move to its own NTR)
   1. State vectors are marshaled to a binary form and stored
   2. Use a storage area with the file naming scheme md5_sha1 for all content
   3. Database used only for relational information (meta data)
5. Makes the man-effort dependent only on the algorithm and not on number of observations or targets as is the current practice.

#### Content
All software architectures and designs start with the dividing the problem into more manageable parts. This architecture divides the problem into four systems: algorithm engine, aspects, persistence, and pipeline management. The algorithm engine is used to compute, for a single target, the values that currently have merit in the field. Aspects use Bayesian statistics with a Bag of Words model to perform meta analysis across the various targets that have been processed with the algorithm engine. Persistence is how the data is stored and accessed. Lastly, the pipeline management is the system that decides what elements of the algorithm engine and aspects need to be executed with which data. Each of these parts uses a Facade Pattern making them plug-n-play with disparate implementations of any of the four systems. For instance, if one decides to do different science with a different data set, then only the algorithm engine requires modification.

Since the access to the algorithm engine is through a Facade Pattern, the pipeline knows nothing about the internal organization, like processing order, of the algorithm engine. Instead, part of the Facade Pattern allows the pipeline management to query the inter-dependencies and compute enough of the Abstract Syntax Tree to determine the order of processing and data dependency of the algorithm elements at run time. Because the pipeline knows which elements depend on which data, when it detects a change in a particular data item, it can then activate all of the algorithm engine elements that depend on that data. The pipeline management can also monitor the algorithm engine element version numbers so that data can be processed when the code changes as well. Both of these combined mean that the minimal but complete set of data is always generated when change is detected within the data or algorithm engine.

One of the key elements that ties all four systems together while maintaining their independence is the state vector. A state vector is simply a container for a collection of values. Traditionally, procedural systems require that input and output data types be defined a priori. In this system, input and output data types are defined a posteriori. In other words, the Facade Patterns specifically allow for the exploration of available state vectors and their content at run time. Making the state vector and its values a posteriori allow for inexpensive refactor of the algorithm engine and meta analysis. The former is important to keep the algorithm engine at the state of the art when it is rapidly changing. The latter is important because it is the meta analysis that transforms the state vectors and values into a probability of interest.

An interesting side effect of the algorithm engine and state vector combination is how the input can act as a manifold at the input tackling the problem of disparate sources. Each source could have its own element within the algorithm engine. The data from each source could be processed uniquely until they reached the same output state vector type. At that point, the processing would become uniform. The algorithm engine does not even require the same number of steps for each of the sources to reach commonality.

Each part of the architecture contributes to making the man-effort of developing an algorithm engine independent of the ever growing number of targets and observations. The algorithm engine is loosely coupled elements that are target and observation independent.

Each implementation of the four systems will have its own NTR when completed.

### Features
*What are the unique features of the software?*

#### Outline
1. Use AI to mine for interesting science
2. Use of reflection to determine algorithm engine dependencies 
2. Recomputation
   1. AST
   2. versioning
   3. data equivalence

#### Content
The three new features of this architecture are: One, the use of AI elements to mine the analysis results from the algorithm engine for aspects that represent new and interesting science. Two, the pipeline management uses reflection to build a dependency tree at run time to determine processing order and needs. Three, the pipeline management uses feedback from the persistence system to optimize algorithm engine computations of analysis results.

The foremost novel idea in this architecture is the inclusion of AI elements to classify analysis results. The primary idea is to use the Bag of Words model with the analysis results and Bayesian statistics to assign a probability of interest. However, the aspects system allows for any type of AI elements for expansion beyond the Bag of Word model to allow for further expansion into the use of AI for classifying science information.

The second and third novel features both relate to the pipeline management system adapting to the algorithm engine system structure and data at run time. The purpose of the pipeline management system is to execute tasks within the algorithm engine to produce required analysis results. Rather than predefine the structure of the algorithm engine or the data (analysis results) that it produces, the Facade Patterns contain reflection like calls for the pipeline management system to retrieve the information it requires at run time. It uses the information to determine order of the tasks to be run. Which tasks need to be run when data changes internally.

From the perspective of the science user, the architecture offers two new features. One, each target is processed uniformly because the algorithm engine is target agnostic. Two, the architecture encourages the use of CBE results based on heuristically derived models. These two feature are the most exciting to the current customer because they have no other tool available to them with either of these features or the ability to add them.


### Improvements
*What improvements have been made over existing similar software application?*

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
- postgresql 9.4
- Python 3.x
- python3-psycopg2
- python3-pydot
- python3-pyfits
- python3-scipy
- python3-twisted
- python3-xlrd




# Algorithm Engine NTR 
## Title
## Contributors
- Al Niessner
- John Livingston
- Udo Wehmeier
- Gael Roudier
- Mark Swain
- Yi Yuan

## Software Description
### Abstract
*The abstract should focus on the programmatic and/or utilization aspects of the software*

### Problem Statement
*What problems are you trying to solve in the software?*

### Accomplishes
*This software accomplishes the following?*

### Features
*What are the unique features of the software?*

### Improvements
*What improvements have been made over existing similar software application?*

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

# Aspect NTR
## Title
## Contributors:
## Software Description
### Abstract
*The abstract should focus on the programmatic and/or utilization aspects of the software*

### Problem Statement
*What problems are you trying to solve in the software?*

### Accomplishes
*This software accomplishes the following?*

### Features
*What are the unique features of the software?*

### Improvements
*What improvements have been made over existing similar software application?*

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

# Persistence NTR 
## Title
## Contributors:
- Al Niessner

## Software Description
### Abstract
*The abstract should focus on the programmatic and/or utilization aspects of the software*

### Problem Statement
*What problems are you trying to solve in the software?*

### Accomplishes
*This software accomplishes the following?*

### Features
*What are the unique features of the software?*

### Improvements
*What improvements have been made over existing similar software application?*

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

# Pipeline NTR 
## Title
## Contributors:
- Al Niessner

## Software Description
### Abstract
*The abstract should focus on the programmatic and/or utilization aspects of the software*

### Problem Statement
*What problems are you trying to solve in the software?*

### Accomplishes
*This software accomplishes the following?*

### Features
*What are the unique features of the software?*

### Improvements
*What improvements have been made over existing similar software application?*

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
