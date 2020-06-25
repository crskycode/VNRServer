using System;
using System.Collections.Generic;
using System.ComponentModel.DataAnnotations;
using System.Linq;
using System.Threading.Tasks;

namespace VisualNovelReaderServer.Models
{
    public class GameNameSubmitParams
    {
        [Required]
        [StringLength(32)]
        public string Type { get; set; }
        [Required]
        [StringLength(1024)]
        public string Value { get; set; }
    }

    public class TextHookSubmitParams
    {
        [Required]
        [StringLength(32)]
        public string Type { get; set; }
        [Required]
        [StringLength(64)]
        public string Name { get; set; }
        [Required]
        [StringLength(64)]
        public string Sig { get; set; }
    }

    public class TextSettingSubmitParams
    {
        [Required]
        [StringLength(16)]
        public string Language { get; set; }
        [Required]
        [StringLength(32)]
        public string Encoding { get; set; }

        [Required]
        public bool KeepAllText { get; set; }
        [Required]
        public bool KeepSpaces { get; set; }
        [Required]
        public bool RemoveRepeat { get; set; }
        [Required]
        public bool IgnoreRepeat { get; set; }

        [Required]
        public TextHookSubmitParams[] Hooks { get; set; }

        [Required]
        [StringLength(300)]
        public string HookCode { get; set; }
    }

    public class GameSubmitParams
    {
        [Required]
        [StringLength(64)]
        public string Username { get; set; }
        [Required]
        [StringLength(64)]
        public string Password { get; set; }

        [Required]
        [StringLength(32)]
        public string Md5 { get; set; }

        //[Required]
        public int? GameItemId { get; set; }

        [Required]
        public GameNameSubmitParams[] Names { get; set; }

        [Required]
        public TextSettingSubmitParams TextSetting { get; set; }
    }

    public class GameSubmitResult
    {
        public int Id { get; set; }
    }

    public class GameQueryParams
    {
        public int? Id { get; set; }

        [StringLength(32)]
        public string Md5 { get; set; }
    }

    public class GameNameResultData
    {
        public string Type { get; set; }
        public string Value { get; set; }
    }

    public class TextHookResultData
    {
        public string Type { get; set; }
        public string Name { get; set; }
        public string Sig { get; set; }
    }

    public class TextSettingResultData
    {
        public string Language { get; set; }
        public string Encoding { get; set; }
        public bool KeepAllText { get; set; }
        public bool KeepSpaces { get; set; }
        public bool RemoveRepeat { get; set; }
        public bool IgnoreRepeat { get; set; }
        public TextHookResultData[] Hooks { get; set; }
        public string HookCode { get; set; }
    }

    public class GameResultData
    {
        public int Id { get; set; }
        public string Md5 { get; set; }
        public int? GameItemId { get; set; }
        public GameNameResultData[] Names { get; set; }
        public TextSettingResultData TextSetting { get; set; }
        public int Comments { get; set; }
    }

    public class GameFileResultData
    {
        public int Id { get; set; }
        public string Md5 { get; set; }
        public int? GameItemId { get; set; }
        public string FileName { get; set; }
        public int Visits { get; set; }
        public int Comments { get; set; }
    }

    public class GameItemResultData
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
    }

    public class ReferenceQueryParams
    {
        public int? GameId { get; set; }

        [StringLength(32)]
        public string GameMd5 { get; set; }
    }

    public class ReferenceResultData
    {
        public int Id { get; set; }
        public string Type { get; set; }
        public int GameId { get; set; }
        public int GameItemId { get; set; }
        public string Title { get; set; }
        public string Brand { get; set; }
        public long Date { get; set; }
        public string Key { get; set; }
        public string Url { get; set; }
        public int CreatorId { get; set; }
        public long CreationTime { get; set; }
    }

    public class GameNameUpdateParams
    {
        [StringLength(32)]
        public string Type { get; set; }
        [StringLength(1024)]
        public string Value { get; set; }
    }

    public class TextHookUpdateParams
    {
        [StringLength(32)]
        public string Type { get; set; }
        [StringLength(64)]
        public string Name { get; set; }
        [StringLength(64)]
        public string Sig { get; set; }

        public bool? Delete { get; set; }
    }

    public class TextSettingUpdateParams
    {
        [StringLength(16)]
        public string Language { get; set; }
        [StringLength(32)]
        public string Encoding { get; set; }

        public bool? KeepAllText { get; set; }
        public bool? KeepSpaces { get; set; }
        public bool? RemoveRepeat { get; set; }
        public bool? IgnoreRepeat { get; set; }

        public TextHookUpdateParams[] Hooks { get; set; }

        [StringLength(300)]
        public string HookCode { get; set; }
    }

    public class GameUpdateParams
    {
        [Required]
        public string Username { get; set; }
        [Required]
        public string Password { get; set; }

        public int? Id { get; set; }

        [StringLength(32)]
        public string Md5 { get; set; }

        public GameNameUpdateParams[] Names { get; set; }
        public TextSettingUpdateParams TextSetting { get; set; }
    }

    public class GameUpdateResult
    {
        public int Id { get; set; }
    }
}
