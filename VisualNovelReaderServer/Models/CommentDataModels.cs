using System;
using System.Collections.Generic;
using System.ComponentModel.DataAnnotations;
using System.Linq;
using System.Threading.Tasks;

namespace VisualNovelReaderServer.Models
{
    public class ContextSubmitParams
    {
        [Required]
        [StringLength(64)]
        public string Hash { get; set; }

        [Required]
        [Range(1, 5)]
        public int Size { get; set; }

        [Required]
        [StringLength(1024)]
        public string Content { get; set; }
    }

    public class CommentSubmitParams
    {
        [Required]
        [StringLength(64)]
        public string Username { get; set; }
        [Required]
        [StringLength(64)]
        public string Password { get; set; }

        //[Required]
        public int? GameId { get; set; }

        [StringLength(32)]
        public string GameMd5 { get; set; }

        [Required]
        public ContextSubmitParams Context { get; set; }

        [Required]
        [StringLength(16)]
        public string Type { get; set; }
        [Required]
        [StringLength(16)]
        public string Language { get; set; }
        [Required]
        [StringLength(1024)]
        public string Text { get; set; }

        //[Required]
        public bool Disabled { get; set; }
        //[Required]
        public bool Locked { get; set; }
        //[Required]
        public bool Deleted { get; set; }

        //[Required]
        [StringLength(300)]
        public string CreationComment { get; set; }

        //[Required]
        [StringLength(300)]
        public string RevisionComment { get; set; }
    }

    public class CommentSubmitResult
    {
        public int Id { get; set; }
    }

    public class CommentQueryParams
    {
        public int? GameId { get; set; }

        [StringLength(32)]
        public string GameMd5 { get; set; }
    }

    public class ContextResultData
    {
        public string Hash { get; set; }
        public int Size { get; set; }
        public string Content { get; set; }
    }

    public class CommentResultData
    {
        public int Id { get; set; }
        public int GameId { get; set; }
        public int? GameItemId { get; set; }
        public ContextResultData Context { get; set; }
        public string Type { get; set; }
        public string Language { get; set; }
        public string Text { get; set; }
        public bool Disabled { get; set; }
        public bool Locked { get; set; }
        public int Liked { get; set; }
        public int Disliked { get; set; }
        public int CreatorId { get; set; }
        public string CreationComment { get; set; }
        public long CreationTime { get; set; }
        public int? EditorId { get; set; }
        public string RevisionComment { get; set; }
        public long RevisionTime { get; set; }
    }

    public class ContextUpdateParams
    {
        [StringLength(64)]
        public string Hash { get; set; }
        [Range(1, 5)]
        public int? Size { get; set; }
        [StringLength(1024)]
        public string Content { get; set; }
    }

    public class CommentUpdateParams
    {
        [Required]
        [StringLength(64)]
        public string Username { get; set; }
        [Required]
        [StringLength(64)]
        public string Password { get; set; }

        [Required]
        public int Id { get; set; }

        public ContextUpdateParams Context { get; set; }

        [StringLength(16)]
        public string Type { get; set; }
        [StringLength(16)]
        public string Language { get; set; }
        [StringLength(1024)]
        public string Text { get; set; }

        public bool? Disabled { get; set; }
        public bool? Locked { get; set; }
        public bool? Deleted { get; set; }
        public int? Liked { get; set; }
        public int? Disliked { get; set; }

        [StringLength(300)]
        public string CreationComment { get; set; }

        [StringLength(300)]
        public string RevisionComment { get; set; }
    }

    public class CommentUpdateResult
    {
        public int Id { get; set; }
    }
}
