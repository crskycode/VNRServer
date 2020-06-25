using System;
using System.Collections.Generic;
using System.Linq;
using System.Reflection;
using System.Threading.Tasks;
using Microsoft.AspNetCore.Cors;
using Microsoft.AspNetCore.Http;
using Microsoft.AspNetCore.Mvc;
using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.Logging;
using VisualNovelReaderServer.Data;
using VisualNovelReaderServer.Models;

namespace VisualNovelReaderServer.Controllers
{
    [Route("api/[controller]")]
    [EnableCors]
    [ApiController]
    public class GameController : ControllerBase
    {
        private readonly ILogger<GameController> _logger;
        private readonly MainDbContext _dbContext;

        public GameController(ILogger<GameController> logger, MainDbContext dbContext)
        {
            _logger = logger;
            _dbContext = dbContext;
        }

        [HttpPost("submit")]
        public async Task<ActionResult<GameSubmitResult>> Submit(GameSubmitParams @params)
        {
            User user = await _dbContext.User
                .Where(it => it.Username == @params.Username && it.Password == @params.Password)
                .FirstOrDefaultAsync();

            if (user == null)
                return Unauthorized();

            user.AccessTime = DateTime.UtcNow;

            Game game = new Game
            {
                Md5 = @params.Md5,
                GameItemId = @params.GameItemId,
                Names = @params.Names.Select(it => new GameName
                {
                    Type = it.Type,
                    Value = it.Value
                }).ToList(),
                TextSetting = new TextSetting
                {
                    Language = @params.TextSetting.Language,
                    Encoding = @params.TextSetting.Encoding,
                    KeepAllText = @params.TextSetting.KeepAllText,
                    KeepSpaces = @params.TextSetting.KeepSpaces,
                    RemoveRepeat = @params.TextSetting.RemoveRepeat,
                    IgnoreRepeat = @params.TextSetting.IgnoreRepeat,
                    Hooks = @params.TextSetting.Hooks.Select(it => new TextHook
                    {
                        Type = it.Type,
                        Name = it.Name,
                        Sig = it.Sig
                    }).ToList(),
                    HookCode = @params.TextSetting.HookCode
                },
                CreatorId = user.Id,
                CreationTime = DateTime.UtcNow,
                ModifiedTime = DateTime.UtcNow
            };

            _dbContext.Game.Add(game);

            await _dbContext.SaveChangesAsync();

            return new GameSubmitResult { Id = game.Id };
        }

        [HttpPost("detail")]
        public async Task<ActionResult<GameResultData>> QueryDetail(GameQueryParams @params)
        {
            Game game = null;

            // Support query by MD5
            if (@params.Md5 != null && @params.Md5.Length == 32)
            {
                game = await _dbContext.Game
                    .Where(it => it.Md5 == @params.Md5)
                    .FirstOrDefaultAsync();
            }
            else
            {
                if (@params.Md5 == null)
                {
                    _logger.LogError("Query: Missing GameId and Md5.");
                    return NotFound();
                }

                game = await _dbContext.Game
                    .Where(it => it.Id == @params.Id)
                    .FirstOrDefaultAsync();
            }

            if (game == null)
            {
                _logger.LogError("Query: Game '{1}' or '{2}' not found.", @params.Id, @params.Md5);
                return NotFound();
            }

            await _dbContext.Entry(game)
                .Collection(it => it.Names).LoadAsync();
            await _dbContext.Entry(game)
                .Reference(it => it.TextSetting).LoadAsync();
            await _dbContext.Entry(game.TextSetting)
                .Collection(it => it.Hooks).LoadAsync();

            return new GameResultData
            {
                Id = game.Id,
                Md5 = game.Md5,
                GameItemId = game.GameItemId,
                Names = game.Names.Select(
                    it => new GameNameResultData
                    {
                        Type = it.Type,
                        Value = it.Value
                    }).ToArray(),
                TextSetting = new TextSettingResultData
                {
                    Language = game.TextSetting.Language,
                    Encoding = game.TextSetting.Encoding,
                    KeepAllText = game.TextSetting.KeepAllText,
                    KeepSpaces = game.TextSetting.KeepSpaces,
                    RemoveRepeat = game.TextSetting.RemoveRepeat,
                    IgnoreRepeat = game.TextSetting.IgnoreRepeat,
                    Hooks = game.TextSetting.Hooks.Select(
                        it => new TextHookResultData
                        {
                            Type = it.Type,
                            Name = it.Name,
                            Sig = it.Sig
                        }).ToArray(),
                    HookCode = game.TextSetting.HookCode
                },
                Comments = 0
            };
        }

        [HttpPost("files")]
        public async Task<ActionResult<IEnumerable<GameFileResultData>>> QueryFiles()
        {
            return await _dbContext.Game
                .OrderBy(it => it.Id)
                .Select(it => new GameFileResultData
                {
                    Id = it.Id,
                    Md5 = it.Md5,
                    GameItemId = it.GameItemId,
                    FileName = it.Names.Where(it => it.Type == "file").Select(it => it.Value).FirstOrDefault(),
                    Visits = 0,
                    Comments = 0
                }).ToArrayAsync();
        }

        [HttpPost("items")]
        public async Task<ActionResult<IEnumerable<GameItemResultData>>> QueryItems()
        {
            return await _dbContext.GameItem
                .OrderBy(it => it.Id)
                .Select(it => new GameItemResultData
                {
                    Id = it.Id,
                    Title = it.Title,
                    RomajiTitle = it.RomajiTitle,
                    Brand = it.Brand,
                    Series = it.Series,
                    ImageUrl = it.ImageUrl,
                    BannerUrl = it.BannerUrl,
                    Wiki = it.Wiki,
                    FileSize = it.FileSize,
                    Tags = it.Tags,
                    Date = it.Date,
                    Artists = it.Artists,
                    SdArtists = it.SdArtists,
                    Writers = it.Writers,
                    Musicians = it.Musicians,
                    Otome = it.Otome,
                    Ecchi = it.Ecchi,
                    Okazu = it.Okazu,
                    TopicCount = it.TopicCount,
                    AnnotCount = it.AnnotCount,
                    SubtitleCount = it.SubtitleCount,
                    PlayUserCount = it.PlayUserCount,
                    ScapeMedian = it.ScapeMedian,
                    ScapeCount = it.ScapeCount,
                    OverallScoreCount = it.OverallScoreCount,
                    OverallScoreSum = it.OverallScoreSum,
                    EcchiScoreCount = it.EcchiScoreCount,
                    EcchiScoreSum = it.EcchiScoreSum,
                }).ToArrayAsync();
        }

        [HttpPost("references")]
        public async Task<ActionResult<IEnumerable<ReferenceResultData>>> QueryReferences(ReferenceQueryParams @params)
        {
            // Support query by MD5
            if (@params.GameMd5 != null && @params.GameMd5.Length == 32)
            {
                Game game = await _dbContext.Game
                    .Where(it => it.Md5 == @params.GameMd5)
                    .FirstOrDefaultAsync();

                if (game == null)
                    return NotFound();

                @params.GameId = game.Id;
            }

            if (@params.GameId == null)
                return BadRequest();

            return await _dbContext.Reference
                .Where(it => it.GameId == @params.GameId)
                .Select(it => new ReferenceResultData
                {
                    Id = it.Id,
                    Type = it.Type,
                    GameId = it.GameId,
                    GameItemId = it.GameItemId,
                    Title = it.Title,
                    Brand = it.Brand,
                    Date = it.Date.ToUnixTimeSeconds(),
                    Key = it.Key,
                    Url = it.Url,
                    CreatorId = it.CreatorId,
                    CreationTime = it.CreationTime.ToUnixTimeSeconds(),
                }).ToArrayAsync();
        }

        [HttpPost("update")]
        public async Task<ActionResult<GameUpdateResult>> Update(GameUpdateParams @params)
        {
            User user = await _dbContext.User
                .Where(it => it.Username == @params.Username && it.Password == @params.Password)
                .FirstOrDefaultAsync();

            if (user == null)
                return Unauthorized();

            user.AccessTime = DateTime.UtcNow;

            Game game = null;

            // Support query by MD5
            if (@params.Md5 != null && @params.Md5.Length == 32)
            {
                game = await _dbContext.Game
                    .Include(it => it.Names)
                    .Include(it => it.TextSetting).ThenInclude(it => it.Hooks)
                    .Where(it => it.Md5 == @params.Md5)
                    .FirstOrDefaultAsync();
            }
            else
            {
                if (@params.Id == null)
                {
                    _logger.LogError("Update: Missing GameId and Md5.");
                    return NotFound();
                }

                game = await _dbContext.Game
                    .Include(it => it.Names)
                    .Include(it => it.TextSetting).ThenInclude(it => it.Hooks)
                    .Where(it => it.Id == @params.Id)
                    .FirstOrDefaultAsync();
            }

            if (game == null)
            {
                if (@params.Md5 == null)
                {
                    _logger.LogError("Update: Missing Md5 for add new game.");
                    return NotFound();
                }

                Game newGame = new Game
                {
                    Md5 = @params.Md5,
                    GameItemId = null,
                    Names = @params.Names.Select(it => new GameName
                    {
                        Type = it.Type,
                        Value = it.Value
                    }).ToList(),
                    TextSetting = new TextSetting
                    {
                        Language = @params.TextSetting.Language,
                        Encoding = @params.TextSetting.Encoding,
                        KeepAllText = @params.TextSetting.KeepAllText ?? false,
                        KeepSpaces = @params.TextSetting.KeepSpaces ?? false,
                        RemoveRepeat = @params.TextSetting.RemoveRepeat ?? false,
                        IgnoreRepeat = @params.TextSetting.IgnoreRepeat ?? false,
                        Hooks = @params.TextSetting.Hooks.Select(it => new TextHook
                        {
                            Type = it.Type,
                            Name = it.Name,
                            Sig = it.Sig
                        }).ToList(),
                        HookCode = @params.TextSetting.HookCode ?? ""
                    },
                    CreatorId = user.Id,
                    CreationTime = DateTime.UtcNow,
                    ModifiedTime = DateTime.UtcNow
                };

                _dbContext.Game.Add(newGame);

                await _dbContext.SaveChangesAsync();

                return new GameUpdateResult { Id = newGame.Id };
            }

            if (user.Id != game.CreatorId)
                return Unauthorized();

            if (@params.Names != null)
            {
                game.Names.Clear();

                GameName[] names = @params.Names.Select(
                    it => new GameName
                    {
                        Type = it.Type,
                        Value = it.Value
                    }).ToArray();

                game.Names.AddRange(names);
            }
            if (@params.TextSetting != null)
            {
                if (@params.TextSetting.Language != null)
                    game.TextSetting.Language = @params.TextSetting.Language;
                if (@params.TextSetting.Encoding != null)
                    game.TextSetting.Encoding = @params.TextSetting.Encoding;
                if (@params.TextSetting.KeepAllText != null)
                    game.TextSetting.KeepAllText = (bool)@params.TextSetting.KeepAllText;
                if (@params.TextSetting.KeepSpaces != null)
                    game.TextSetting.KeepSpaces = (bool)@params.TextSetting.KeepSpaces;
                if (@params.TextSetting.RemoveRepeat != null)
                    game.TextSetting.RemoveRepeat = (bool)@params.TextSetting.RemoveRepeat;
                if (@params.TextSetting.IgnoreRepeat != null)
                    game.TextSetting.IgnoreRepeat = (bool)@params.TextSetting.IgnoreRepeat;

                if (@params.TextSetting.Hooks != null)
                {
                    game.TextSetting.Hooks.Clear();

                    TextHook[] hooks = @params.TextSetting.Hooks
                        .Where(it => it.Delete != true)
                        .Select(it => new TextHook
                        {
                            Type = it.Type,
                            Name = it.Name,
                            Sig = it.Sig,
                        }).ToArray();

                    game.TextSetting.Hooks.AddRange(hooks);
                }

                if (@params.TextSetting.HookCode != null)
                    game.TextSetting.HookCode = @params.TextSetting.HookCode;
            }

            game.ModifiedTime = DateTime.UtcNow;

            await _dbContext.SaveChangesAsync();

            return new GameUpdateResult { Id = game.Id };
        }
    }
}
