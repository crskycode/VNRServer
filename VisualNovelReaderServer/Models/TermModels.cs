using System;
using System.Collections.Generic;
using System.Globalization;
using System.Linq;
using System.Threading.Tasks;

namespace VisualNovelReaderServer.Models
{
    /// <summary>
    /// Table
    /// </summary>
    public class Term
    {
        /// <summary>
        /// </summary>
        public int Id { get; set; }

        /// <summary>
        /// </summary>
        public string FromLanguage { get; set; }

        /// <summary>
        /// </summary>
        public string ToLanguage { get; set; }

        /// <summary>
        /// </summary>
        public string Type { get; set; }

        /// <summary>
        /// Translator name
        /// Apply the term to the specified translator.
        /// </summary>
        public string Translators { get; set; }

        /// <summary>
        /// Context type
        /// Apply the term to the specified context.
        /// </summary>
        public string ContextType { get; set; }

        /// <summary>
        /// Foreign key
        /// Apply the term to the specified game.
        /// </summary>
        public int? GameId { get; set; }

        /// <summary>
        /// Navigation Property
        /// </summary>
        public Game Game { get; set; }

        /// <summary>
        /// Apply the term to the specified game.
        /// </summary>
        public bool IsSpecial { get; set; }

        /// <summary>
        /// Only visible to yourself.
        /// </summary>
        public bool IsPrivate { get; set; }

        /// <summary>
        /// </summary>
        public bool IsHentai { get; set; }

        /// <summary>
        /// </summary>
        public bool IsRegex { get; set; }

        /// <summary>
        /// </summary>
        public bool IsPhrase { get; set; }

        /// <summary>
        /// </summary>
        public bool IgnoreCase { get; set; }

        /// <summary>
        /// </summary>
        public bool Disabled { get; set; }

        /// <summary>
        /// </summary>
        public bool Deleted { get; set; }

        /// <summary>
        /// </summary>
        public int Priority { get; set; }

        /// <summary>
        /// </summary>
        public string Role { get; set; }

        /// <summary>
        /// </summary>
        public string Pattern { get; set; }

        /// <summary>
        /// </summary>
        public string Text { get; set; }

        /// <summary>
        /// </summary>
        public string Ruby { get; set; }

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
}
