using System;
using System.Collections.Generic;
using System.ComponentModel.DataAnnotations;
using System.Linq;
using System.Threading.Tasks;

namespace VisualNovelReaderServer.Models
{
    public class TermQueryParams
    {
        [Required]
        [StringLength(64)]
        public string Username { get; set; }
        [Required]
        [StringLength(64)]
        public string Password { get; set; }
    }

    public class TermResultData
    {
        public int Id { get; set; }
        public string FromLanguage { get; set; }
        public string ToLanguage { get; set; }
        public string Type { get; set; }
        public string Translators { get; set; }
        public string ContextType { get; set; }
        public int? GameId { get; set; }
        public bool IsSpecial { get; set; }
        public bool IsPrivate { get; set; }
        public bool IsHentai { get; set; }
        public bool IsRegex { get; set; }
        public bool IsPhrase { get; set; }
        public bool IgnoreCase { get; set; }
        public bool Disabled { get; set; }
        public int Priority { get; set; }
        public string Role { get; set; }
        public string Pattern { get; set; }
        public string Text { get; set; }
        public string Ruby { get; set; }
        public int CreatorId { get; set; }
        public string CreationComment { get; set; }
        public long CreationTime { get; set; }
        public int? EditorId { get; set; }
        public string RevisionComment { get; set; }
        public long RevisionTime { get; set; }
    }

    public class TermQueryResult
    {
        public long Timestamp { get; set; }
        public TermResultData[] Terms { get; set; }
    }

    public class TermSubmitParams
    {
        [Required]
        [StringLength(64)]
        public string Username { get; set; }
        [Required]
        [StringLength(64)]
        public string Password { get; set; }

        [StringLength(16)]
        public string FromLanguage { get; set; }
        [StringLength(16)]
        public string ToLanguage { get; set; }
        [StringLength(16)]
        public string Type { get; set; }
        [StringLength(80)]
        public string Translators { get; set; }
        [StringLength(16)]
        public string ContextType { get; set; }

        //[Required]
        public int? GameId { get; set; }

        [StringLength(32)]
        public string GameMd5 { get; set; }

        [Required]
        public bool IsSpecial { get; set; }
        [Required]
        public bool IsPrivate { get; set; }
        [Required]
        public bool IsHentai { get; set; }
        [Required]
        public bool IsRegex { get; set; }
        [Required]
        public bool IsPhrase { get; set; }
        [Required]
        public bool IgnoreCase { get; set; }
        [Required]
        public bool Disabled { get; set; }
        [Required]
        public int Priority { get; set; }
        [Required]
        public bool Deleted { get; set; }

        [StringLength(500)]
        public string Role { get; set; }
        [StringLength(500)]
        public string Pattern { get; set; }
        [StringLength(500)]
        public string Text { get; set; }
        [StringLength(500)]
        public string Ruby { get; set; }
        [StringLength(300)]
        public string CreationComment { get; set; }
        [StringLength(300)]
        public string RevisionComment { get; set; }
    }

    public class TermSubmitResult
    {
        public int Id { get; set; }
    }

    public class TermUpdateParams
    {
        [Required]
        [StringLength(64)]
        public string Username { get; set; }
        [Required]
        [StringLength(64)]
        public string Password { get; set; }

        [Required]
        public int Id { get; set; }

        [StringLength(16)]
        public string FromLanguage { get; set; }
        [StringLength(16)]
        public string ToLanguage { get; set; }
        [StringLength(16)]
        public string Type { get; set; }
        [StringLength(80)]
        public string Translators { get; set; }
        [StringLength(16)]
        public string ContextType { get; set; }

        public int? GameId { get; set; }
        public bool? IsSpecial { get; set; }
        public bool? IsPrivate { get; set; }
        public bool? IsHentai { get; set; }
        public bool? IsRegex { get; set; }
        public bool? IsPhrase { get; set; }
        public bool? IgnoreCase { get; set; }
        public bool? Disabled { get; set; }
        public bool? Deleted { get; set; }
        public int? Priority { get; set; }

        [StringLength(500)]
        public string Role { get; set; }
        [StringLength(500)]
        public string Pattern { get; set; }
        [StringLength(500)]
        public string Text { get; set; }
        [StringLength(500)]
        public string Ruby { get; set; }
        [StringLength(300)]
        public string RevisionComment { get; set; }
    }

    public class TermUpdateResult
    {
        public int Id { get; set; }
    }
}
