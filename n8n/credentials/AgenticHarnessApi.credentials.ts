import {
  ICredentialType,
  INodeProperties,
} from 'n8n-workflow';

export class AgenticHarnessApi implements ICredentialType {
  name = 'agenticHarnessApi';
  displayName = 'Agentic Harness API';
  documentationUrl = 'https://github.com/sahiixx/agentic-harness-integration';

  properties: INodeProperties[] = [
    {
      displayName: 'Base URL',
      name: 'baseUrl',
      type: 'string',
      default: 'http://localhost:8000',
      placeholder: 'http://localhost:8000',
      description: 'Base URL of the Agentic Harness Bridge API',
    },
    {
      displayName: 'API Key',
      name: 'apiKey',
      type: 'string',
      typeOptions: { password: true },
      default: '',
      description: 'Optional API key if authentication is enabled',
    },
  ];
}
