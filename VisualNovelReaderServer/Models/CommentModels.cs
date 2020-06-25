using Microsoft.EntityFrameworkCore;
using Microsoft.EntityFrameworkCore.Metadata;
using System;
using System.Collections.Generic;
using System.Linq;
using System.Security.Permissions;
using System.Threading.Tasks;

namespace VisualNovelReaderServer.Models
{
    /// <summary>
    /// Table
    /// </summary>
    public class Comment
    {
        /// <summary>
        /// </summary>
        public int Id { get; set; }

        /// <summary>
        /// Foreign key
        /// </summary>
        public int GameId { get; set; }

        /// <summary>
        /// Navigation Property
        /// </summary>
        public Game Game { get; set; }

        /// <summary>
        /// Foreign key
        /// </summary>
        public int? GameItemId { get; set; }

        /// <summary>
        /// Navigation Property
        /// </summary>
        public GameItem GameItem { get; set; }

        /// <summary>
        /// </summary>
        public Context Context { get; set; }

        /// <summary>
        /// </summary>
        public string Type { get; set; }

        /// <summary>
        /// </summary>
        public string Language { get; set; }

        /// <summary>
        /// </summary>
        public string Text { get; set; }

        /// <summary>
        /// </summary>
        public bool Disabled { get; set; }

        /// <summary>
        /// </summary>
        public bool Locked { get; set; }

        /// <summary>
        /// </summary>
        public bool Deleted { get; set; }

        /// <summary>
        /// </summary>
        public int Liked { get; set; }

        /// <summary>
        /// </summary>
        public int Disliked { get; set; }

        /// <summary>
        /// Foreign key
        /// </summary>
        public int CreatorId { get; set; }

        /// <summary>
        /// Navigation Property
        /// </summary>
        public User Creator { get; set; }

        /// <summary>
        /// </summary>
        public string CreationComment { get; set; }

        /// <summary>
        /// </summary>
        public DateTime CreationTime { get; set; }

        /// <summary>
        /// Foreign key
        /// </summary>
        public int? EditorId { get; set; }

        /// <summary>
        /// Navigation Property
        /// </summary>
        public User Editor { get; set; }

        /// <summary>
        /// </summary>
        public string RevisionComment { get; set; }

        /// <summary>
        /// </summary>
        public DateTime RevisionTime { get; set; }
    }

    /// <summary>
    /// Text context of the comment.
    /// </summary>
    [Owned]
    public class Context
    {
        /// <summary>
        /// </summary>
        public string Hash { get; set; }
        
        /// <summary>
        /// </summary>
        public int Size { get; set; }

        /// <summary>
        /// </summary>
        public string Content { get; set; }
    }
}
