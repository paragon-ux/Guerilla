# Related Work and Comparative Positioning

## 1. Overview

Guerilla lies at the intersection of provenance modeling, data-lineage infrastructure, workflow orchestration, event-sourced systems, version-control architectures, distributed tracing, software-supply-chain attestation, and persistent agent runtimes. Each of these fields addresses part of the continuity problem. Provenance standards describe how entities, activities, and actors are related. Workflow engines coordinate predefined tasks. Data catalogs maintain metadata and dataset lineage. Event-sourced systems preserve state-changing events. Version-control systems represent immutable revisions. Distributed tracing records request execution across services. Agent frameworks maintain conversation state, checkpoints, or execution traces.

Guerilla combines selected mechanisms from these areas but assigns them a different architectural role. Its primary object is one logically authoritative, append-only causal-lineage DAG spanning heterogeneous external systems. The graph records artifact revisions, observations, operations, events, evaluations, decisions, conflicts, snapshots, and typed relationships. External systems continue to own their application state, validation rules, concurrency mechanisms, and native revisions.

The distinguishing contribution is therefore not the use of graphs, provenance, append-only records, or adapters in isolation. It is the coordinated use of these mechanisms to provide cross-system continuity without replacing the systems of record.

---

## 2. Provenance Models and Standards

### 2.1 W3C PROV

The W3C PROV family is the closest conceptual foundation for Guerilla’s provenance model. PROV-DM represents provenance through entities, activities, agents, and relationships such as generation, use, derivation, attribution, association, and delegation (Moreau & Missier, 2013). Its central concern is explaining how an object came to exist and which activities and actors influenced it.

Guerilla and PROV share several characteristics:

* both represent provenance explicitly rather than relying on narrative logs;
* both distinguish artifacts or entities from the activities that operate on them;
* both record actors and responsibility;
* both support derivation and dependency relationships;
* both permit provenance information to be exchanged independently of the originating application.

The systems differ in purpose and runtime responsibility. PROV is principally a provenance representation framework. It does not prescribe a single append-only graph authority, an action-invocation protocol, adapter capability negotiation, external-state freshness rules, idempotency, or recovery after an uncertain external action.

Guerilla introduces these operational mechanisms around its provenance graph. It records action intent before requesting an external mutation, preserves accepted, rejected, partial, and unknown outcomes, and supports reconciliation when execution is interrupted. It also defines explicit state boundaries so that a provenance observation does not imply ownership of the observed application state.

PROV may serve as an interchange or conceptual mapping layer for Guerilla. For example, Guerilla artifact nodes can map to PROV entities, operations to activities, and actors to agents. However, a complete mapping would need Guerilla-specific extensions for graph revisions, snapshots, state boundaries, adapter capabilities, conflicts, idempotency, and external-action reconciliation.

### 2.2 Open Provenance Model

The Open Provenance Model preceded W3C PROV and similarly represented causal dependencies among artifacts, processes, and agents (Moreau et al., 2011). Its objective was interoperability among provenance systems rather than active orchestration.

Like Guerilla, the Open Provenance Model recognizes that provenance should be represented separately from application-specific execution details. Guerilla extends this separation by defining which parts of the integrated environment remain authoritative outside the provenance layer.

The principal difference is that Guerilla treats provenance as part of a continuity runtime. The graph is not merely an explanatory record exported after execution. It is consulted before subsequent operations, used to determine stale observations and unresolved conflicts, and employed to construct resumable workflow boundaries.

### 2.3 Scientific Workflow Provenance

Scientific workflow systems such as VisTrails were designed to capture workflow evolution, parameter changes, executions, and resulting artifacts (Freire et al., 2006). These systems demonstrated that preserving only final outputs is insufficient for reproducibility; the evolution of the workflow itself must also be recorded.

Guerilla shares the emphasis on workflow evolution and immutable revision history. A superseded plan, rejected result, failed evaluation, or abandoned branch remains part of the lineage rather than being overwritten.

The difference is architectural scope. Scientific workflow provenance is normally tied to a workflow environment and its execution model. Guerilla is designed as an overlay across systems that may use transactional services, filesystems, source-control histories, event streams, batch jobs, manual reviews, or agent-driven tools. It does not require those systems to execute within one workflow runtime.

---

## 3. Data Lineage and Metadata Platforms

### 3.1 OpenLineage and Marquez

OpenLineage defines an extensible event model for communicating lineage metadata about jobs, runs, and datasets. Marquez provides a reference implementation and metadata service around that model. These systems are especially relevant because they collect lineage from heterogeneous processing tools through integrations rather than replacing the tools themselves.

Similarities with Guerilla include:

* adapter- or integration-based ingestion;
* stable identities for producers, executions, and outputs;
* event-oriented lineage capture;
* separation between operational tools and lineage metadata;
* centralized or logically unified lineage queries;
* extensible metadata fields.

The primary difference is domain breadth and continuity semantics. OpenLineage is centered on data-processing jobs, runs, and datasets. Guerilla generalizes the graph to requirements, source records, documents, decisions, model outputs, reviews, conflicts, snapshots, and other artifact types.

Guerilla also defines action intent, external mutation outcomes, reconciliation, state-boundary ownership, graph revisions, and workflow-resume semantics. An OpenLineage run event reports what occurred in a data pipeline; a Guerilla operation may also participate in deciding what should happen next, which observations must be refreshed, and which unresolved conflict prevents continuation.

OpenLineage events could be ingested through a Guerilla adapter. In that arrangement, OpenLineage would remain the producer of domain-specific job and dataset metadata, while Guerilla would connect those records to broader goals, decisions, artifacts, and external processes.

### 3.2 Apache Atlas and DataHub

Apache Atlas and DataHub represent enterprise metadata, classifications, schemas, ownership, and lineage. They use graph-oriented models to make relationships among datasets, services, users, and other metadata entities searchable and governable.

These platforms resemble Guerilla in their use of:

* typed entities and relationships;
* metadata ingestion connectors;
* centralized identity resolution;
* lineage traversal;
* search and derived user interfaces;
* policy and governance metadata.

Their authoritative objects differ. Metadata catalogs primarily manage descriptive metadata and governance information about organizational data assets. Guerilla manages causal workflow lineage and continuity records.

A catalog may state that a table is produced by a pipeline and owned by a team. Guerilla can additionally record which observation of the upstream state informed a particular operation, which external action produced a specific revision, which evaluation failed, which decision selected a remediation branch, and which snapshot captured the resulting continuation point.

Metadata graphs are also not necessarily strict causal DAGs. They may contain reciprocal ownership, classification, membership, or semantic relationships. Guerilla preserves a strict DAG for direct authoritative relationships. Symmetric or potentially cyclic domain relationships are represented as reified event or conflict nodes and displayed through non-authoritative projections.

---

## 4. Workflow Orchestration and Durable Execution

### 4.1 Apache Airflow and Comparable DAG Schedulers

Apache Airflow represents workflows as DAGs of tasks and uses a scheduler and executor to run them. Similar systems include Prefect and other task-oriented orchestration platforms.

The visual similarity between an Airflow DAG and the Guerilla graph conceals a difference in meaning. A workflow DAG generally represents an execution plan: which task should run after which prerequisite. Guerilla’s DAG represents committed lineage: which observation, operation, event, artifact revision, evaluation, conflict, or decision causally preceded another record.

A workflow definition may be reused for many executions. Guerilla records the particular revisions and results involved in each execution and may connect them to activities outside the scheduler.

Airflow and similar orchestrators usually own or coordinate the execution lifecycle of their tasks. Guerilla does not require control of external execution. It may observe a scheduler, invoke it through an adapter, or ingest its results while preserving the scheduler as the authority for task state.

### 4.2 Dagster and Asset-Oriented Orchestration

Dagster models data and software-defined assets, their dependencies, materializations, and observations. This asset-centered model is closer to Guerilla than purely task-centered orchestration because it emphasizes the artifacts produced rather than only the tasks executed.

Both approaches recognize:

* dependency relationships among artifacts;
* materialization or production events;
* observations of externally managed assets;
* typed metadata;
* graph-derived operational views.

Dagster nevertheless remains an execution and data-orchestration platform whose graph is strongly connected to the assets and computations it manages. Guerilla is intended to connect artifacts and operations across several unrelated execution environments.

Guerilla additionally includes decisions, conflicts, evaluations, graph snapshots, external authority boundaries, and uncertain-action reconciliation as first-class elements. These records allow it to represent continuity even when no single orchestrator controls the complete workflow.

### 4.3 Temporal and Durable Workflow Runtimes

Temporal and related durable-execution systems retain workflow event histories so that long-running operations can survive process failure and resume. Their deterministic replay, retry policies, and durable timers address many of the reliability problems encountered in agentic systems.

Similarities with Guerilla include:

* persistence beyond one process or conversation;
* explicit event histories;
* recovery after interruption;
* durable operation identity;
* retry and idempotency concerns;
* separation of workflow intent from individual worker processes.

The central difference is ownership. A durable workflow engine generally owns workflow execution state and requires operations to conform to its programming and replay model. Guerilla does not become the execution-state authority for every integrated system. It records that an external system was observed, invoked, evaluated, or reconciled, while leaving the external system’s state and transaction rules intact.

Temporal histories are typically scoped to individual workflow executions. Guerilla instead maintains one logical lineage graph across workflows, tools, artifacts, and state boundaries. A Temporal workflow could therefore be one external system represented through a Guerilla adapter.

---

## 5. Event Sourcing and Append-Only Architectures

Event sourcing stores state-changing events as the authoritative record and reconstructs application state by replaying those events (Fowler, 2005). Guerilla adopts the append-only and immutable-history principles of event sourcing, including the idea that corrections should be represented by later records rather than destructive updates.

The similarity ends at the state-ownership boundary. In event-sourced applications, the event stream normally is the application-state authority. Replaying it reconstructs the application’s current state.

Guerilla replay reconstructs only the lineage graph. It does not replay external mutations, rebuild every external application, regenerate a repository, repeat a deployment, or reproduce a human decision process. Refreshing an external system requires a new explicit observation or action.

Event streams also provide order but do not necessarily provide complete causal structure. Guerilla requires typed edges to represent causation, dependency, derivation, evidence, evaluation, supersession, resolution, and snapshot inclusion. Temporal proximity alone is insufficient to create an edge.

---

## 6. Version Control and Content-Addressed Histories

Git is an important architectural analogue because it uses immutable, content-addressed objects and a commit DAG to preserve revision history (Chacon & Straub, 2014). Branching, convergence, hashes, parent relationships, and reproducible repository revisions all resemble elements of Guerilla’s graph model.

The main similarities are:

* immutable committed records;
* content hashes;
* revision ancestry;
* branching and convergence;
* explicit supersession through later revisions;
* local-first operation;
* reconstructable history.

Git’s authority is limited to repository objects and references. It does not natively record the complete relationship among an external requirement, a service observation, a model decision, a test result, a human review, and a deployment. Commit messages may describe some of this context, but the relationships are not uniformly typed or machine-verifiable.

Guerilla can reference Git commits as artifact revisions while connecting them to non-repository events and decisions. It also distinguishes graph revision from artifact revision: a commit may be one artifact revision observed at a particular Guerilla graph revision.

Data and model versioning systems such as DVC similarly combine repository metadata, content-addressed storage, and pipeline dependencies. Their emphasis is reproducibility within data and machine-learning workflows. Guerilla addresses a wider range of artifacts and does not require the external artifact store or repository to adopt Guerilla’s persistence model.

---

## 7. Experiment Tracking and Machine-Learning Lifecycle Systems

MLflow and comparable experiment-tracking systems record runs, parameters, metrics, artifacts, model versions, and deployment-related metadata (Zaharia et al., 2018). They provide valuable continuity across model-development activities.

Guerilla shares the use of stable run or operation identities, artifact references, evaluations, revisions, and derived status views. An ML experiment, model version, or evaluation report can be represented as an external artifact or operation.

The systems differ in domain and authority. MLflow is designed around the machine-learning lifecycle and may own experiment and model-registry state. Guerilla is domain-independent and records causal relationships across external systems without becoming their universal experiment, artifact, or registry store.

Guerilla’s decision and conflict nodes also make it possible to distinguish a measured evaluation from the later human or policy decision to accept a model. This separation is often compressed into one lifecycle stage in domain-specific registries.

---

## 8. Distributed Tracing and Observability

OpenTelemetry defines common telemetry structures for traces, metrics, and logs. A distributed trace associates spans through parent context and links, allowing operators to reconstruct how one request propagated across services.

Tracing and Guerilla share:

* cross-system correlation;
* actor or service attribution;
* timestamps;
* parent or causal relationships;
* identifiers that survive process boundaries;
* derived visualization and search.

Distributed tracing is generally optimized for operational diagnosis of request execution. Traces may be sampled, retained temporarily, and organized around service calls. They do not normally represent durable artifact revisions, human decisions, supersession, external-state ownership, workflow snapshots, or long-term planning dependencies.

Guerilla also distinguishes correlation from causation. Two records may share a workflow correlation identifier without being connected by an authoritative causal edge. Trace data can be ingested as evidence, but it does not automatically define the complete lineage graph.

---

## 9. Software-Supply-Chain Provenance

The in-toto framework records software-supply-chain steps, functionaries, materials, and products, allowing consumers to verify that required steps occurred and were performed by authorized parties (Torres-Arias et al., 2019). Related attestation frameworks similarly associate artifacts with builders, inputs, and policies.

Guerilla and in-toto share:

* artifact provenance;
* stable step or operation identities;
* materials and products;
* actor attribution;
* integrity hashes;
* externally verifiable records;
* policy-aware evaluation.

The difference is purpose. Supply-chain provenance is oriented toward security attestations and verification of release processes. Guerilla addresses general workflow continuity, including incomplete work, stale observations, branch selection, failed evaluations, unresolved conflicts, and future operations.

Supply-chain attestations may become high-value artifact or evaluation nodes in Guerilla. Guerilla could connect a signed build attestation to the requirement, source revision, review decision, test results, and deployment operation that surround it.

---

## 10. Knowledge Graphs

Knowledge graphs provide flexible representations of entities and semantically typed relationships (Hogan et al., 2021). They support integration across heterogeneous schemas and can expose multiple query-specific views.

This flexibility resembles Guerilla’s typed-node and typed-relationship model. Both can connect objects that originate in different domains and use stable identifiers to support traversal.

A general knowledge graph, however, does not necessarily impose immutability, append-only commitment, causal direction, strict acyclicity, state-boundary ownership, or graph-revision semantics. It may contain cyclic and symmetric domain relationships as direct edges.

Guerilla is therefore more constrained than a general knowledge graph. Its restrictions are intentional: they make causal ancestry, revision history, topological planning, and snapshot reconstruction unambiguous. Domain relations that do not fit the DAG are reified and rendered through derived views.

Guerilla may still export selected records into RDF or another knowledge-graph representation, but such an export would be a projection rather than a replacement lineage authority.

---

## 11. Agent-Orchestration, Memory, and Trace Systems

Research on multi-agent systems and persistent language-model applications has introduced conversation histories, memory stores, tool-call traces, checkpoints, and graph-based execution. AutoGen, for example, coordinates several agents through structured conversation (Wu et al., 2023). MemGPT addresses finite model context through hierarchical memory management (Packer et al., 2023). Generative Agents maintains a memory stream and derives reflections and plans from recorded experience (Park et al., 2023).

These systems share Guerilla’s motivation to preserve continuity beyond a single model response. They recognize that agent behavior depends on earlier observations, actions, and stored context.

Their primary stored object is usually model-centered: a conversation, memory item, tool trace, plan, checkpoint, or agent state. Guerilla’s primary object is system-centered causal lineage across agents, tools, artifacts, repositories, services, and human decisions.

Guerilla also does not treat an agent’s internal memory or summary as authoritative external state. A model-generated evaluation is labeled as a model evaluation, including provenance and confidence where appropriate. It does not overwrite a deterministic test result, an external revision, or a human decision.

An agent framework can use Guerilla as a continuity substrate. The agent runtime may still own scheduling, prompts, memory retrieval, and model execution, while Guerilla records the externalized goals, observations, operations, results, conflicts, and decisions relevant to cross-system work.

---

## 12. Comparative Matrix

| Related system or research area              | Primary authoritative object                                 | Similarities to Guerilla                                                 | Principal differences from Guerilla                                                                                                                         |
| -------------------------------------------- | ------------------------------------------------------------ | ------------------------------------------------------------------------ | ----------------------------------------------------------------------------------------------------------------------------------------------------------- |
| W3C PROV                                     | Provenance statements about entities, activities, and agents | Typed provenance, derivation, attribution, actor representation          | Representation standard rather than a complete continuity runtime; no required action reconciliation, state-boundary negotiation, or single append-only DAG |
| Open Provenance Model                        | Artifact-process-agent provenance graph                      | Causal dependencies and interoperable provenance                         | Focused on provenance exchange rather than active orchestration and resume behavior                                                                         |
| VisTrails and scientific workflow provenance | Workflow definitions, revisions, and execution provenance    | Workflow evolution, reproducibility, immutable history                   | Usually tied to a particular scientific workflow environment                                                                                                |
| OpenLineage and Marquez                      | Jobs, runs, datasets, and lineage events                     | Adapter-based ingestion, producer-consumer lineage, extensibility        | Primarily data-pipeline lineage; lacks Guerilla’s generalized decisions, conflicts, snapshots, and cross-domain continuity                                  |
| Apache Atlas and DataHub                     | Enterprise metadata and governance graph                     | Typed entities, lineage traversal, ingestion integrations, catalog views | Metadata catalog rather than causal workflow authority; graph may include non-causal cycles and semantic associations                                       |
| Airflow and task DAG schedulers              | Executable workflow definition and task state                | DAG dependencies, execution history, retries                             | DAG describes planned execution under scheduler control rather than cross-system immutable lineage                                                          |
| Dagster                                      | Assets, computations, observations, and materializations     | Asset dependencies, observations, graph-derived views                    | Asset and data orchestration runtime; narrower authority and domain than Guerilla                                                                           |
| Temporal and durable workflow engines        | Durable workflow event history                               | Resumability, retries, idempotency, failure recovery                     | Own workflow execution state and replay; histories are normally workflow-scoped rather than one cross-system lineage authority                              |
| Event sourcing                               | Application event stream                                     | Append-only history, replay, immutable correction                        | Event stream normally owns application state; Guerilla replay reconstructs lineage only                                                                     |
| Git                                          | Content-addressed repository DAG                             | Immutable revisions, hashes, branching, convergence                      | Repository-scoped; lacks generalized external observations, evaluations, decisions, and state boundaries                                                    |
| DVC and data-versioning systems              | Data artifacts and pipeline dependencies                     | Content addressing, reproducible artifacts, dependency graphs            | Focused on repository-based data and ML workflows                                                                                                           |
| MLflow                                       | Experiments, runs, metrics, artifacts, and model versions    | Operation identities, evaluations, artifacts, lifecycle views            | Domain-specific lifecycle system rather than architecture-agnostic lineage overlay                                                                          |
| OpenTelemetry                                | Traces, spans, metrics, and logs                             | Cross-process identifiers, causal context, operational views             | Request-observability focus; often sampled and temporary; does not represent complete artifact and decision continuity                                      |
| in-toto                                      | Signed supply-chain steps, materials, and products           | Artifact provenance, actors, hashes, policy verification                 | Security-attestation focus rather than open-ended workflow continuation                                                                                     |
| Knowledge graphs                             | Entities and semantic relationships                          | Heterogeneous integration, typed relations, graph queries                | No inherent append-only, DAG, authority-boundary, or revision guarantees                                                                                    |
| Agent memory and orchestration systems       | Conversation, agent state, memory, or execution trace        | Persistent context, tool histories, checkpoints, planning                | Model-centric continuity; generally not an authoritative cross-system causal graph                                                                          |

---

## 13. Guerilla’s Distinguishing Combination

The comparison indicates that Guerilla does not occupy a completely isolated research category. It combines established ideas from several mature fields. Its differentiating position arises from the following combination.

### 13.1 One logical lineage authority

Guerilla assigns authoritative causal relationship ownership to one logical graph. External systems may maintain their own histories, but a relationship represented as Guerilla lineage is not independently owned by several projections or adapters.

### 13.2 Preservation of external state authority

Unlike a universal event store or workflow engine, Guerilla does not require external application state to be reconstructed from its graph. An external database, repository, service, filesystem, or manual process remains authoritative within its declared state boundary.

### 13.3 Strict DAG with reified non-DAG relationships

Rather than weakening acyclicity to accommodate every domain relationship, Guerilla represents symmetric, cyclic, or non-causal assertions as nodes. This preserves unambiguous causal ordering while allowing projections to render richer domain relationships.

### 13.4 Operational provenance

Guerilla links provenance to action intent, invocation, result, reconciliation, evaluation, conflict, and decision. It therefore extends beyond descriptive lineage into continuity management.

### 13.5 Explicit uncertainty and failure

Rejected actions, stale observations, incomplete lineage, uncertain outcomes, and failed evaluations are first-class records. They are not removed from the graph when a later branch succeeds.

### 13.6 Separation of outcome layers

Guerilla distinguishes transport completion, external-system acceptance, evaluation outcome, conflict state, and goal-completion decision. This avoids reducing several independent judgments to one status value.

### 13.7 Capability-aware adapters

Adapters declare consistency, concurrency, event ordering, replay, snapshot, identity, idempotency, and lineage-completeness characteristics. Guerilla therefore does not assume that all integrations provide transactional reads, stable identities, ordered events, or reliable replay.

### 13.8 Source-bound derived views

A view identifies its source graph revision, query, policy version, transformation version, freshness, and information loss. The architecture consequently supports many representations without allowing them to become competing sources of lineage truth.

---

## 14. Research Gap

Existing work provides strong solutions for individual parts of the problem:

* provenance standards describe derivation and attribution;
* workflow systems provide durable execution;
* data-lineage systems connect jobs and datasets;
* metadata catalogs organize enterprise assets;
* event sourcing preserves application events;
* version-control systems preserve immutable revisions;
* observability systems trace service execution;
* supply-chain systems provide verifiable artifact attestations;
* agent frameworks preserve model-centered memory and execution state.

The remaining gap is an architecture that combines these concerns while preserving heterogeneous systems of record.

Guerilla addresses this gap by treating lineage continuity as a separate authority layer. The proposed system is intended to answer questions such as:

* Which observation of an external revision justified this operation?
* Which actor and adapter requested the external action?
* What outcome did the external authority report?
* Which artifact revision resulted?
* Which evaluation assessed that revision?
* Which unresolved conflict currently blocks continuation?
* Which decision selected the active branch?
* Which observations must be refreshed before resumption?
* Which manifest, snapshot, or status view was generated from which graph revision?

No claim of absolute novelty should be made solely from this conceptual comparison. A systematic literature review and implementation-level comparison would be required to determine whether an existing platform already provides the complete combination of strict single-DAG authority, heterogeneous state-boundary preservation, uncertain-action reconciliation, reified non-DAG relationships, and source-bound projections.

---

## 15. Implications for Guerilla’s Design

The related literature suggests several opportunities for interoperability.

First, Guerilla should support mappings to W3C PROV so that selected provenance can be exchanged with existing systems. Second, OpenLineage events should be ingestible as domain-specific lineage observations. Third, distributed traces and supply-chain attestations should be treated as external evidence rather than duplicated operational truth. Fourth, workflow engines should be integrated through adapters rather than reimplemented. Fifth, manifests and snapshots should use content hashes and stable revision identifiers comparable to those used by version-control and reproducibility systems.

The literature also identifies design risks. A graph that attempts to become a universal metadata catalog may lose its causal precision. A runtime that assumes control of external execution may violate its state boundaries. A status projection that omits its source revision may become a hidden authority. An append-only graph without reconciliation may record intent while missing the external result. An overly permissive graph model may introduce cycles that make dependency and resume calculations ambiguous.

Guerilla’s architecture should therefore remain deliberately constrained: one logical graph authority, immutable revisions, typed causal relationships, explicit external ownership, capability-aware adapters, evidence-backed conflicts, and regenerable projections.

---

## References

Apache Software Foundation. (n.d.). *Apache Airflow documentation*. https://airflow.apache.org/docs/

Apache Software Foundation. (n.d.). *Apache Atlas*. https://atlas.apache.org/

Chacon, S., & Straub, B. (2014). *Pro Git* (2nd ed.). Apress. https://git-scm.com/book/en/v2

DataHub Project. (n.d.). *DataHub documentation*. https://datahubproject.io/docs/

Dagster Labs. (n.d.). *Dagster documentation*. https://docs.dagster.io/

Fowler, M. (2005). Event sourcing. https://martinfowler.com/eaaDev/EventSourcing.html

Freire, J., Silva, C. T., Callahan, S. P., Santos, E., Scheidegger, C. E., & Vo, H. T. (2006). Managing rapidly-evolving scientific workflows. In *Provenance and Annotation of Data* (pp. 10–18). Springer. https://doi.org/10.1007/11890850_2

Hogan, A., Blomqvist, E., Cochez, M., D’Amato, C., Melo, G. de, Gutierrez, C., Kirrane, S., Gayo, J. E. L., Navigli, R., Neumaier, S., Ngomo, A.-C. N., Polleres, A., Rashid, S. M., Rula, A., Schmelzeisen, L., Sequeda, J., Staab, S., & Zimmermann, A. (2021). Knowledge graphs. *ACM Computing Surveys, 54*(4), Article 71. https://doi.org/10.1145/3447772

Linux Foundation AI & Data. (n.d.). *OpenLineage specification*. https://openlineage.io/docs/spec/

Marquez Project. (n.d.). *Marquez*. https://marquezproject.ai/

Moreau, L., Clifford, B., Freire, J., Futrelle, J., Gil, Y., Groth, P., Kwasnikowska, N., Miles, S., Missier, P., Myers, J., Plale, B., Simmhan, Y., Stephan, E., & Van den Bussche, J. (2011). The Open Provenance Model core specification. *Future Generation Computer Systems, 27*(6), 743–756. https://doi.org/10.1016/j.future.2010.07.005

Moreau, L., & Missier, P. (Eds.). (2013). *PROV-DM: The PROV data model*. W3C Recommendation. https://www.w3.org/TR/prov-dm/

OpenTelemetry Authors. (n.d.). *OpenTelemetry specification*. https://opentelemetry.io/docs/specs/otel/

Packer, C., Fang, V., Patil, S. G., Lin, K., Wooders, S., & Gonzalez, J. E. (2023). MemGPT: Towards LLMs as operating systems. *arXiv*. https://arxiv.org/abs/2310.08560

Park, J. S., O’Brien, J. C., Cai, C. J., Morris, M. R., Liang, P., & Bernstein, M. S. (2023). Generative agents: Interactive simulacra of human behavior. In *Proceedings of the 36th Annual ACM Symposium on User Interface Software and Technology*. https://doi.org/10.1145/3586183.3606763

Temporal Technologies. (n.d.). *Temporal documentation*. https://docs.temporal.io/

Torres-Arias, S., Afzali, H., Kuppusamy, T. K., Curtmola, R., & Cappos, J. (2019). in-toto: Providing farm-to-table guarantees for bits and bytes. In *Proceedings of the 28th USENIX Security Symposium* (pp. 1393–1410). https://www.usenix.org/conference/usenixsecurity19/presentation/torres-arias

Wu, Q., Bansal, G., Zhang, J., Wu, Y., Li, B., Zhu, E., Jiang, L., Zhang, X., Zhang, S., Liu, J., Awadallah, A. H., White, R. W., Burger, D., & Wang, C. (2023). AutoGen: Enabling next-generation LLM applications via multi-agent conversation. *arXiv*. https://arxiv.org/abs/2308.08155

Zaharia, M., Chen, A., Davidson, A., Ghodsi, A., Hong, S. A., Konwinski, A., Murching, S., Nykodym, T., Ogilvie, P., Parkhe, M., Xie, F., & Zumar, C. (2018). Accelerating the machine learning lifecycle with MLflow. *IEEE Data Engineering Bulletin, 41*(4), 39–45.
