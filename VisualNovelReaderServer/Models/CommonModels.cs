using Microsoft.EntityFrameworkCore;
using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;

namespace VisualNovelReaderServer.Models
{
    public class AppVersion
    {
        public string Name { get; set; }
        public long Timestamp { get; set; }
    }
}
