using Azure.Core;
using Azure.Identity;
using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace TesterConsole
{
    public static class Foundry
    {
        public static async Task<string> GetFoundryAccessTokenAsync()
        {
            // REST docs specify this scope for the Evaluations API.
            var credential = new DefaultAzureCredential();
            var ctx = new TokenRequestContext(new[] { "https://ai.azure.com/.default" });
            AccessToken token = await credential.GetTokenAsync(ctx);
            return token.Token;
        }
    }
}
