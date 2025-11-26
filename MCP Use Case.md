# MCP Use Case: Querying Data Beyond the UI

## Executive Summary

This document demonstrates how the Model Context Protocol (MCP) enables AI assistants to retrieve information that is not readily accessible through a traditional web UI, providing a powerful alternative to building custom UI features or writing manual database queries.

## The Scenario

### The Question
**What are the articles posted by 'Danielle Hernandez' with the tag 'laugh'**

This is a simple, natural language question that a user might ask about content in the Conduit application (a RealWorld spec blogging platform).

### The UI Limitation

The Conduit web UI provides the following pages:
- **Home page** - Shows global feed or personalized feed
- **Article detail** - Shows individual article with comments
- **Profile page** - Shows user profile with authored/favorited articles tabs
- **Settings** - User account management
- **Auth pages** - Login/Register

To answer "What are the books posted by Angela Mcdaniel?" using the traditional UI:

1. You would need to navigate to `/profile/Danielle%20Hernandez`
2. View the "Authored articles" tab
3. Manually scroll through the list
4. Look for the articles tagged with "laugh"

**Problems with this approach:**
- Requires multiple clicks and navigation steps
- Time-consuming for users
- Doesn't provide a quick summary
- Limited by pagination (only shows a subset at a time)
- Requires the UI to have been built with this specific feature

### Traditional Alternatives

#### Option 1: Extend the UI
You could build a new UI feature:
- Create a new search page
- Add filters for authors
- Implement pagination and sorting
- Design and style the components
- Write frontend and backend code
- Test across browsers
- Maintain the feature

**Cost:** Days to weeks of development time

#### Option 2: Direct Database Query
You could write a SQL query directly:

```sql
SELECT 
    a.id,
    a.slug,
    a.title,
    a.description,
    a.body,
    a.created_at,
    a.updated_at,
    u.name as author_name,
    u.bio as author_bio,
    u.image as author_image,
    COUNT(DISTINCT af.user_id) as favorites_count,
    ARRAY_AGG(DISTINCT t.name) FILTER (WHERE t.name IS NOT NULL) as tag_list
FROM articles a
INNER JOIN users u ON a.author_id = u.id
LEFT JOIN article_favorite af ON af.article_id = a.id
INNER JOIN article_tag at ON at.article_id = a.id
INNER JOIN tags t ON t.id = at.tag_id
WHERE u.name = 'Danielle Hernandez'
  AND a.id IN (
    SELECT at2.article_id 
    FROM article_tag at2
    INNER JOIN tags t2 ON t2.id = at2.tag_id
    WHERE t2.name = 'laugh'
  )
GROUP BY a.id, a.slug, a.title, a.description, a.body, a.created_at, a.updated_at, 
         u.name, u.bio, u.image
ORDER BY a.created_at DESC;
```

**Problems with this approach:**
- Requires database access and credentials
- Needs SQL expertise
- Requires understanding the database schema
- Security concerns (direct database access)
- Not user-friendly for non-technical users
- Manual process every time you need the information

## The MCP Solution

### What is MCP?

**Model Context Protocol (MCP)** is an open protocol that standardizes how AI assistants connect to data sources and tools. It allows AI models to:

- Access external APIs
- Query databases
- Execute tools and functions
- Retrieve real-time information

Think of MCP as a universal adapter that lets AI assistants "plug into" various systems and data sources.

### How MCP Works in This Case

In this implementation, we've configured MCP to expose the Conduit API through an OpenAPI specification:

1. **OpenAPI Specification** (`api.json`)
   - Defines all available API endpoints
   - Documents parameters, request bodies, and responses
   - Includes authentication requirements

2. **MCP Configuration** (`vscode_mcp.json`)
   - Registers the OpenAPI specification as an MCP server
   - Makes API endpoints available as callable tools
   - Handles authentication and request formatting

3. **AI Assistant Integration**
   - The AI assistant (GitHub Copilot with Claude Sonnet 4.5) has access to MCP tools
   - It can understand natural language queries
   - It translates questions into appropriate API calls
   - It formats and presents the results

### The Interaction Flow

```
User Question: "What are the books posted by Angela Mcdaniel?"
                              ↓
AI Assistant interprets the question and identifies:
  - Need: Get articles by a specific author
  - Author name: "Angela Mcdaniel"
                              ↓
AI looks through available MCP tools and finds:
  - Tool: mcp_demo-openapi_GetArticles
  - Parameter: author (optional query parameter)
                              ↓
AI executes the tool:
  GET /api/articles?author=Angela%20Mcdaniel
                              ↓
API returns JSON response with articles array filtering for the tag 'laugh'
                              ↓
AI processes and formats the response into human-readable form
                              ↓
User receives: Clear list of 2 articles with titles and descriptions
```

### The Result

When asked **"What are the articles posted by 'Danielle Hernandez' with the tag 'laugh'**, the AI assistant:

1. **Automatically identified** the appropriate API endpoint (`GetArticles`)
2. **Applied the correct filter** (`author=Angela Mcdaniel`)
3. **Called the API** through MCP
4. **Received structured data** (7 articles with full metadata)
5. **Applies the tag filter** ('laugh') on the returned articles
5. **Formatted the response** into a readable summary

**Response time:** Seconds

**User effort:** Ask a simple question in natural language

**Result delivered:**
```
Danielle Hernandez has posted 2 articles with the tag "laugh":

Discover around author - About job opportunities and paper topics. Tags: add, current, laugh. (5 favorites)

Early artist available - Discussing western views and degrees. Tags: just, laugh. (1 favorite)

Both articles were created on November 24, 2025.
```

## Technology Stack

### Components

1. **FastAPI Backend**
   - RESTful API following RealWorld spec
   - OpenAPI documentation auto-generated
   - Token-based authentication
   - Endpoints for articles, users, profiles, comments, tags

2. **OpenAPI Specification**
   - JSON schema defining all API operations
   - Parameter definitions and validation rules
   - Authentication scheme documentation
   - Response schemas

3. **MCP Server**
   - Bridges the OpenAPI specification to the AI assistant
   - Translates API definitions into callable tools
   - Handles request/response formatting
   - Manages authentication headers

4. **AI Assistant (GitHub Copilot)**
   - Natural language understanding
   - Tool selection and parameter inference
   - Result formatting and presentation
   - Context awareness

### Alternative MCP Implementations

While this use case demonstrates MCP through an **OpenAPI layer**, MCP can also work with:

#### Direct Database and OpenAPU Access
```json
// In your MCP client config (e.g. ChatGPT / Claude / Cursor)
{
  "servers": {
    "demo-openapi": {
      "command": "uvx",
      "args": ["awslabs.openapi-mcp-server@latest"],
      "env": {
        "API_NAME": "demo-api",
        "API_BASE_URL": "http://localhost:8000/api",
        "API_SPEC_URL": "http://localhost:8000/api/docs.json",
        "LOG_LEVEL": "ERROR",
        "ENABLE_OPERATION_PROMPTS": "true"
      }
    },
    "postgres": {
      "type": "stdio",
      "command": "npx",
      "args": ["-y", "mcp-postgres-server"],
      "env": {
        "PG_HOST": "localhost",
        "PG_PORT": "5433",
        "PG_USER": "main",
        "PG_PASSWORD": "main",
        "PG_DATABASE": "main"
      }
    }
  }
}

```

This would allow the AI to:
- Execute SQL queries directly
- Access data not exposed by the API
- Perform complex analytical queries
- Join across tables as needed

#### Other MCP Servers
- **Filesystem MCP** - Read/write files
- **Git MCP** - Access repository history
- **Brave Search MCP** - Web search capabilities
- **Custom MCP servers** - Any tool or data source

## Key Benefits

### 1. No UI Development Required
- No need to build search interfaces
- No frontend components to design
- No pagination logic to implement
- Instant access to all API capabilities

### 2. Natural Language Interface
- Users ask questions in plain English
- No need to learn UI navigation
- No need to understand API documentation
- Accessible to non-technical users

### 3. Flexibility
- Ask any question the API can answer
- Combine multiple queries
- Get different views of the same data
- No predefined use cases required

### 4. Speed
- Answers in seconds
- No manual navigation
- No need to write SQL
- Immediate results

### 5. Consistency
- Uses official API
- Respects authentication and permissions
- Same business logic as the UI
- No data inconsistencies

### 6. Discoverability
- AI understands available operations
- Suggests related queries
- Combines multiple data sources
- Adapts to new API endpoints automatically

## Real-World Applications

### Content Management
- "Show me all articles tagged with 'technology' from the last week"
- "Which users have the most favorited articles?"
- "Find articles similar to 'Water past think'"

### User Analytics
- "Who are the top 10 contributors this month?"
- "Which articles have the most engagement?"
- "Show me users who follow Angela Mcdaniel"

### Moderation
- "Find articles with no tags"
- "Show users who haven't posted in 6 months"
- "List all comments on articles about politics"

### Business Intelligence
- "What are the trending tags this week?"
- "Calculate average favorites per article by author"
- "Show user growth over time"

## Comparison Matrix

| Approach | Setup Time | Query Time | Technical Skill | Flexibility | Maintenance |
|----------|-----------|------------|-----------------|-------------|-------------|
| **Build UI Feature** | Days-Weeks | Seconds | High | Low | Ongoing |
| **Direct SQL** | Minutes | Seconds | Expert | High | None |
| **MCP + AI** | Hours (one-time) | Seconds | None | Very High | Minimal |

## Security Considerations

### API Layer (Current Implementation)
✅ Respects API authentication  
✅ Honors permission boundaries  
✅ Rate limiting applied  
✅ Audit trail in API logs  
✅ No direct database access  

### Database Layer (Alternative)
⚠️ Requires database credentials  
⚠️ Can bypass business logic  
⚠️ Needs careful permission scoping  
⚠️ Should be read-only for safety  
✅ Can access data not in API  

## Conclusion

The Model Context Protocol transforms how users interact with applications by enabling natural language queries against structured data sources. Instead of building custom UI features or writing manual database queries, MCP allows AI assistants to act as an intelligent interface layer.

In this use case, a simple question—**"What are the books posted by Angela Mcdaniel?"**—was answered in seconds through:
- Natural language understanding
- Automatic API endpoint selection
- Proper parameter formatting
- Result synthesis and presentation

This demonstrates MCP's power to:
1. **Reduce development overhead** - No custom UI needed
2. **Improve user experience** - Natural language queries
3. **Increase data accessibility** - Any API call available instantly
4. **Maintain security** - Respects existing authentication/authorization

As AI assistants become more prevalent, MCP provides the standardized foundation for connecting them to the data and tools they need to be truly helpful.

