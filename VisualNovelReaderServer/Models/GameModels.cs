using Microsoft.AspNetCore.Mvc;
using Microsoft.EntityFrameworkCore;
using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.ComponentModel.DataAnnotations;
using System.ComponentModel.DataAnnotations.Schema;
using System.Linq;
using System.Security.Permissions;
using System.Threading.Tasks;

namespace VisualNovelReaderServer.Models
{
    public class GameName
    {
        public int Id { get; set; }
        public string Type { get; set; }
        public string Value { get; set; }
    }

    public class TextHook
    {
        public int Id { get; set; }
        public string Type { get; set; }
        public string Name { get; set; }
        public string Sig { get; set; }
    }

    public class TextSetting
    {
        public int Id { get; set; }
        public string Language { get; set; }
        public string Encoding { get; set; }
        public bool KeepAllText { get; set; }
        public bool KeepSpaces { get; set; }
        public bool RemoveRepeat { get; set; }
        public bool IgnoreRepeat { get; set; }
        public List<TextHook> Hooks { get; set; }
        public string HookCode { get; set; }
    }

    public class Game
    {
        public int Id { get; set; }
        public string Md5 { get; set; }
        public int? GameItemId { get; set; }
        public GameItem GameItem { get; set; }
        public List<GameName> Names { get; set; }
        public int TextSettingId { get; set; }
        public TextSetting TextSetting { get; set; }
        public int CreatorId { get; set; }
        public User Creator { get; set; }
        public DateTime CreationTime { get; set; }
        public DateTime ModifiedTime { get; set; }
    }

    public class GameItem
    {
        public int Id { get; set; }
        public string Title { get; set; }
        public string RomajiTitle { get; set; }
        public string Brand { get; set; }
        public string Series { get; set; }
        public string ImageUrl { get; set; }
        public string BannerUrl { get; set; }
        public string Wiki { get; set; }
        public long FileSize { get; set; }
        public string Tags { get; set; }
        public string Date { get; set; }
        public string Artists { get; set; }
        public string SdArtists { get; set; }
        public string Writers { get; set; }
        public string Musicians { get; set; }
        public bool Otome { get; set; }
        public bool Ecchi { get; set; }
        public bool Okazu { get; set; }
        public int TopicCount { get; set; }
        public int AnnotCount { get; set; }
        public int SubtitleCount { get; set; }
        public int PlayUserCount { get; set; }
        public int ScapeMedian { get; set; }
        public int ScapeCount { get; set; }
        public int OverallScoreCount { get; set; }
        public int OverallScoreSum { get; set; }
        public int EcchiScoreCount { get; set; }
        public int EcchiScoreSum { get; set; }
        public int CreatorId { get; set; }
        public User Creator { get; set; }
        public DateTime CreationTime { get; set; }
        public DateTime ModifiedTime { get; set; }
    }

    public class Reference
    {
        public int Id { get; set; }
        public string Type { get; set; }
        public int GameId { get; set; }
        public Game Game { get; set; }
        public int GameItemId { get; set; }
        public GameItem GameItem { get; set; }
        public string Title { get; set; }
        public string Brand { get; set; }
        public DateTime Date { get; set; }
        public string Key { get; set; }
        public string Url { get; set; }
        public int CreatorId { get; set; }
        public User Creator { get; set; }
        public DateTime CreationTime { get; set; }
        public DateTime ModifiedTime { get; set; }
    }
}
