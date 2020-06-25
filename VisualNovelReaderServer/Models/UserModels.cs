using Microsoft.AspNetCore.Mvc;
using System;
using System.Collections.Generic;
using System.ComponentModel.DataAnnotations;
using System.Linq;
using System.Threading.Tasks;

namespace VisualNovelReaderServer.Models
{
    /// <summary>
    /// Table
    /// </summary>
    public class User
    {
        /// <summary>
        /// Primary Key
        /// </summary>
        public int Id { get; set; }

        /// <summary>
        /// The permissions that this user has.
        /// </summary>
        public int Permissions { get; set; }

        /// <summary>
        /// The user's login name.
        /// </summary>
        public string Username { get; set; }

        /// <summary>
        /// The user's login password.
        /// </summary>
        public string Password { get; set; }

        /// <summary>
        /// The user's email address.
        /// </summary>
        public string Email { get; set; }

        /// <summary>
        /// Other information about the user.
        /// </summary>
        public string ExtraInfo { get; set; }

        /// <summary>
        /// The language used by this user.
        /// </summary>
        public string Language { get; set; }

        /// <summary>
        /// The user's gender.
        /// </summary>
        public string Gender { get; set; }

        /// <summary>
        /// The user's avatar (file token).
        /// </summary>
        public string Avatar { get; set; }

        /// <summary>
        /// The user's homepage url.
        /// </summary>
        public string HomePage { get; set; }

        /// <summary>
        /// The color used by the user's subtitles or comments. (Hexadecimal color code)
        /// </summary>
        public string Color { get; set; }

        /// <summary>
        /// </summary>
        public DateTime CreationTime { get; set; }

        /// <summary>
        /// </summary>
        public DateTime AccessTime { get; set; }

        /// <summary>
        /// </summary>
        public DateTime ModifiedTime { get; set; }
    }
}
