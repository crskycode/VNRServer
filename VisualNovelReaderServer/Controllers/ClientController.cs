using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;
using Microsoft.AspNetCore.Http;
using Microsoft.AspNetCore.Mvc;
using VisualNovelReaderServer.Models;

namespace VisualNovelReaderServer.Controllers
{
    [Route("api/[controller]")]
    [ApiController]
    public class ClientController : ControllerBase
    {
        [HttpGet("version")]
        public ActionResult<IEnumerable<AppVersion>> QueryVersion()
        {
            return new AppVersion[]
            {
                new AppVersion()
                {
                    Name = "vnr",
                    Timestamp = new DateTimeOffset(DateTime.UtcNow).ToUnixTimeSeconds()
                }
            };
        }
    }
}