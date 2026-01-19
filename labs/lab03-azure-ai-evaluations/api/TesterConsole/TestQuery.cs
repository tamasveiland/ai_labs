namespace TesterConsole
{
    public class InputQuery
    {
        public string Query { get; set; } = string.Empty;
        public string Response { get; set; } = string.Empty;
        public List<ToolCall> ToolCalls { get; set; } = new();
        public List<ToolDefinition> ToolDefinitions { get; set; } = new();
    }

    public class ToolCall
    {
        public string Name { get; set; } = string.Empty;
        public Dictionary<string, object> Arguments { get; set; } = new();
    }

    public class ToolDefinition
    {
        public string Name { get; set; } = string.Empty;
        public string Description { get; set; } = string.Empty;
        public ToolParameters Parameters { get; set; } = new();
    }

    public class ToolParameters
    {
        public string Type { get; set; } = string.Empty;
        public Dictionary<string, PropertyDefinition> Properties { get; set; } = new();
        public List<string> Required { get; set; } = new();
    }

    public class PropertyDefinition
    {
        public string Type { get; set; } = string.Empty;
        public string Description { get; set; } = string.Empty;
        public List<string>? Enum { get; set; }
    }
}

