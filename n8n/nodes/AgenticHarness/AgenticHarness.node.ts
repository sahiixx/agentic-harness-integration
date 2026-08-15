import {
  IExecuteFunctions,
  INodeExecutionData,
  INodeType,
  INodeTypeDescription,
  NodeConnectionType,
} from 'n8n-workflow';

export class AgenticHarness implements INodeType {
  description: INodeTypeDescription = {
    displayName: 'Agentic Harness',
    name: 'agenticHarness',
    icon: 'file:AgenticHarness.svg',
    group: ['transform'],
    version: 1,
    subtitle: '={{$parameter["operation"]}}',
    description: 'Call Agentic Harness Bridge endpoints',
    defaults: {
      name: 'Agentic Harness',
    },
    inputs: [NodeConnectionType.Main],
    outputs: [NodeConnectionType.Main],
    credentials: [
      {
        name: 'agenticHarnessApi',
        required: true,
      },
    ],
    properties: [
      {
        displayName: 'Operation',
        name: 'operation',
        type: 'options',
        noDataExpression: true,
        options: [
          {
            name: 'Chain',
            value: 'chain',
            description: 'Prompt chaining pattern',
            action: 'Chain prompts',
          },
          {
            name: 'Route',
            value: 'route',
            description: 'Routing pattern',
            action: 'Route input',
          },
          {
            name: 'Parallel',
            value: 'parallel',
            description: 'Parallelization pattern',
            action: 'Run tasks in parallel',
          },
          {
            name: 'Orchestrate',
            value: 'orchestrate',
            description: 'Orchestrator-workers pattern',
            action: 'Orchestrate workers',
          },
          {
            name: 'Evaluate Optimize',
            value: 'evaluate_optimize',
            description: 'Evaluator-optimizer pattern',
            action: 'Evaluate and optimize',
          },
          {
            name: 'ReAct',
            value: 'react',
            description: 'ReAct reasoning pattern',
            action: 'Run ReAct agent',
          },
          {
            name: 'Reflect',
            value: 'reflect',
            description: 'Reflection pattern',
            action: 'Reflect on draft',
          },
          {
            name: 'NEXUS Enrich',
            value: 'nexus_enrich',
            description: 'NEXUS lead enrichment',
            action: 'Enrich lead',
          },
          {
            name: 'GapClaw Hunt',
            value: 'gapclaw_hunt',
            description: 'GapClaw autonomous research',
            action: 'Run GapClaw hunt',
          },
          {
            name: 'SARA Generate',
            value: 'sara_generate',
            description: 'SARA video script generation',
            action: 'Generate script with SARA',
          },
          {
            name: 'GapSolver Discover',
            value: 'gapsolver_discover',
            description: 'GapSolver gap discovery',
            action: 'Discover gaps',
          },
        ],
        default: 'chain',
      },
      {
        displayName: 'Payload JSON',
        name: 'payload',
        type: 'json',
        default: '{}',
        description: 'JSON payload to send to the endpoint',
        displayOptions: {
          show: {
            operation: [
              'chain',
              'route',
              'parallel',
              'orchestrate',
              'evaluate_optimize',
              'react',
              'reflect',
              'nexus_enrich',
              'gapclaw_hunt',
              'sara_generate',
              'gapsolver_discover',
            ],
          },
        },
      },
    ],
  };

  async execute(this: IExecuteFunctions): Promise<INodeExecutionData[][]> {
    const items = this.getInputData();
    const returnData: INodeExecutionData[] = [];

    const credentials = await this.getCredentials('agenticHarnessApi');
    const baseUrl = (credentials.baseUrl as string).replace(/\/$/, '');
    const apiKey = credentials.apiKey as string;

    const operation = this.getNodeParameter('operation', 0) as string;

    const endpointMap: Record<string, string> = {
      chain: '/pattern/chain',
      route: '/pattern/route',
      parallel: '/pattern/parallel',
      orchestrate: '/pattern/orchestrate',
      evaluate_optimize: '/pattern/evaluate_optimize',
      react: '/pattern/react',
      reflect: '/pattern/reflect',
      nexus_enrich: '/nexus/enrich',
      gapclaw_hunt: '/gapclaw/hunt',
      sara_generate: '/sara/generate',
      gapsolver_discover: '/gapsolver/discover',
    };

    for (let i = 0; i < items.length; i++) {
      const payloadStr = this.getNodeParameter('payload', i) as string;
      const payload = JSON.parse(payloadStr || '{}');

      const headers: Record<string, string> = {
        'Content-Type': 'application/json',
      };
      if (apiKey) {
        headers['Authorization'] = `Bearer ${apiKey}`;
      }

      const response = await this.helpers.request({
        method: 'POST',
        url: `${baseUrl}${endpointMap[operation]}`,
        headers,
        body: payload,
        json: true,
      });

      returnData.push({
        json: response,
      });
    }

    return [returnData];
  }
}
